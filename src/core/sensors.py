"""Cross-platform system sensors used by the UI."""

from __future__ import annotations

import logging
import platform
import shutil
import subprocess
import threading
import time
from typing import Any

import psutil

logger = logging.getLogger(__name__)

# A Windows GPU-counter probe slower than this serves cached values between
# rare retries instead of stalling every sample.
GPU_PROBE_SLOW_SECONDS = 0.2
GPU_PROBE_BACKOFF_SECONDS = 30.0


class SensorReader:
    """Collect metrics and calculate network throughput between reads."""

    def __init__(self) -> None:
        self._network = psutil.net_io_counters()
        self._network_time = time.monotonic()
        self._nvidia_smi = shutil.which("nvidia-smi")  # PATH scan once; presence is fixed per run.
        self._wmi_cimv2 = None  # COM objects are created lazily and reused per thread.
        self._wmi_thermal = None
        self._gpu_values = {"usage": None, "temperature": None}
        self._gpu_next_probe = 0.0

    def _cimv2(self):
        if self._wmi_cimv2 is None:
            import wmi  # type: ignore[import-not-found]

            self._wmi_cimv2 = wmi.WMI(namespace=r"root\cimv2")
        return self._wmi_cimv2

    def _thermal(self):
        if self._wmi_thermal is None:
            import wmi  # type: ignore[import-not-found]

            self._wmi_thermal = wmi.WMI(namespace=r"root\wmi")
        return self._wmi_thermal

    def _temperatures(self) -> dict[str, float | None]:
        cpu: float | None = None
        gpu: float | None = None
        try:
            groups = psutil.sensors_temperatures(fahrenheit=False)
        except (AttributeError, OSError):
            groups = {}
        for name, entries in groups.items():
            for entry in entries:
                label = f"{name} {entry.label}".lower()
                if gpu is None and any(key in label for key in ("gpu", "amdgpu", "radeon")):
                    gpu = round(float(entry.current), 1)
                elif cpu is None and any(key in label for key in ("cpu", "core", "package", "k10temp")):
                    cpu = round(float(entry.current), 1)

        if platform.system() == "Windows" and cpu is None:
            try:
                readings = self._thermal().MSAcpi_ThermalZoneTemperature()
                if readings:
                    cpu = round((float(readings[0].CurrentTemperature) / 10) - 273.15, 1)
            except Exception as error:  # noqa: BLE001 - WMI exposes provider-specific COM errors.
                logger.debug("Windows temperature sensor unavailable: %s", error)
        return {"cpu": cpu, "gpu": gpu}

    def _gpu(self) -> dict[str, float | None]:
        """Read NVIDIA CLI metrics, then vendor-neutral Windows counters."""
        if self._nvidia_smi:
            try:
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=utilization.gpu,temperature.gpu", "--format=csv,noheader,nounits"],
                    capture_output=True,
                    check=True,
                    text=True,
                    timeout=2,
                )
                usage, temperature = result.stdout.splitlines()[0].split(",", maxsplit=1)
                self._gpu_values = {"usage": float(usage.strip()), "temperature": float(temperature.strip())}
                return dict(self._gpu_values)
            except (OSError, subprocess.SubprocessError, ValueError, IndexError):
                pass
        if platform.system() == "Windows":
            now = time.monotonic()
            if now >= self._gpu_next_probe:
                started = time.perf_counter()
                try:
                    engines = self._cimv2().query(
                        "SELECT Name, UtilizationPercentage"
                        " FROM Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine WHERE Name LIKE '%engtype_3D%'"
                    )
                    usage = sum(float(engine.UtilizationPercentage or 0) for engine in engines)
                    # An empty counter set means nothing usable was exposed.
                    self._gpu_values = (
                        {"usage": min(100.0, usage), "temperature": None}
                        if engines
                        else {"usage": None, "temperature": None}
                    )
                except Exception as error:  # noqa: BLE001 - WMI exposes provider-specific COM errors.
                    logger.debug("Windows GPU counters unavailable: %s", error)
                    self._gpu_values = {"usage": None, "temperature": None}
                elapsed = time.perf_counter() - started
                if elapsed > GPU_PROBE_SLOW_SECONDS:
                    self._gpu_next_probe = time.monotonic() + GPU_PROBE_BACKOFF_SECONDS
                    logger.debug(
                        "Slow GPU probe (%.0f ms); caching values for %.0f s",
                        elapsed * 1000,
                        GPU_PROBE_BACKOFF_SECONDS,
                    )
            return dict(self._gpu_values)
        return {"usage": None, "temperature": None}

    @staticmethod
    def _disks() -> dict[str, float]:
        disks: dict[str, float] = {}
        for partition in psutil.disk_partitions(all=False):
            if "cdrom" in partition.opts.lower():
                continue
            try:
                label = partition.device.rstrip("\\/") or partition.mountpoint
                disks[label] = psutil.disk_usage(partition.mountpoint).percent
            except (OSError, PermissionError):
                continue
        return disks

    def _network_rates(self) -> dict[str, float]:
        current = psutil.net_io_counters()
        now = time.monotonic()
        elapsed = max(now - self._network_time, 0.001)
        rates = {
            "upload": max(0.0, (current.bytes_sent - self._network.bytes_sent) / elapsed),
            "download": max(0.0, (current.bytes_recv - self._network.bytes_recv) / elapsed),
        }
        self._network = current
        self._network_time = now
        return rates

    @staticmethod
    def _cancelled(stop: threading.Event | None) -> bool:
        return stop is not None and stop.is_set()

    def get_all(self, stop: threading.Event | None = None) -> dict[str, Any]:
        # Cooperative cancellation: once stopped, skip the remaining heavy
        # probes so shutdown never waits on an in-flight slow provider.
        gpu = {"usage": None, "temperature": None}
        temperatures = {"cpu": None, "gpu": None}
        disks: dict[str, float] = {}
        if not self._cancelled(stop):
            gpu = self._gpu()
            temperatures = self._temperatures()
            disks = self._disks()
        if gpu["temperature"] is not None:
            temperatures["gpu"] = gpu["temperature"]
        return {
            "cpu": psutil.cpu_percent(),
            "ram": psutil.virtual_memory().percent,
            "disks": disks,
            "temps": temperatures,
            "gpu": gpu,
            "network": self._network_rates(),
        }


_reader = SensorReader()


def get_all_sensors() -> dict[str, Any]:
    """Return all metrics in the stable schema consumed by Glint widgets."""
    return _reader.get_all()
