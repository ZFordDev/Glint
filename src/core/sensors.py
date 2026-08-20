"""Cross-platform system sensors used by the UI."""

from __future__ import annotations

import logging
import platform
import shutil
import subprocess
import time
from typing import Any

import psutil

logger = logging.getLogger(__name__)


class SensorReader:
    """Collect metrics and calculate network throughput between reads."""

    def __init__(self) -> None:
        self._network = psutil.net_io_counters()
        self._network_time = time.monotonic()

    @staticmethod
    def _temperatures() -> dict[str, float | None]:
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
                import wmi  # type: ignore[import-not-found]

                readings = wmi.WMI(namespace=r"root\wmi").MSAcpi_ThermalZoneTemperature()
                if readings:
                    cpu = round((float(readings[0].CurrentTemperature) / 10) - 273.15, 1)
            except Exception as error:  # noqa: BLE001 - WMI exposes provider-specific COM errors.
                logger.debug("Windows temperature sensor unavailable: %s", error)
        return {"cpu": cpu, "gpu": gpu}

    @staticmethod
    def _gpu() -> dict[str, float | None]:
        """Read NVIDIA CLI metrics, then vendor-neutral Windows counters."""
        if shutil.which("nvidia-smi"):
            try:
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=utilization.gpu,temperature.gpu", "--format=csv,noheader,nounits"],
                    capture_output=True,
                    check=True,
                    text=True,
                    timeout=2,
                )
                usage, temperature = result.stdout.splitlines()[0].split(",", maxsplit=1)
                return {"usage": float(usage.strip()), "temperature": float(temperature.strip())}
            except (OSError, subprocess.SubprocessError, ValueError, IndexError):
                pass
        if platform.system() == "Windows":
            try:
                import wmi  # type: ignore[import-not-found]

                engines = wmi.WMI(namespace=r"root\cimv2").Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine()
                usage = sum(
                    float(engine.UtilizationPercentage or 0) for engine in engines if "engtype_3D" in engine.Name
                )
                return {"usage": min(100.0, usage), "temperature": None}
            except Exception as error:  # noqa: BLE001 - WMI exposes provider-specific COM errors.
                logger.debug("Windows GPU counters unavailable: %s", error)
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

    def get_all(self) -> dict[str, Any]:
        gpu = self._gpu()
        temperatures = self._temperatures()
        if gpu["temperature"] is not None:
            temperatures["gpu"] = gpu["temperature"]
        return {
            "cpu": psutil.cpu_percent(),
            "ram": psutil.virtual_memory().percent,
            "disks": self._disks(),
            "temps": temperatures,
            "gpu": gpu,
            "network": self._network_rates(),
        }


_reader = SensorReader()


def get_all_sensors() -> dict[str, Any]:
    """Return all metrics in the stable schema consumed by Glint widgets."""
    return _reader.get_all()
