import psutil
import wmi

# Optional: OpenHardwareMonitor support
try:
    import clr  # pythonnet
    clr.AddReference("OpenHardwareMonitorLib")
    from OpenHardwareMonitor.Hardware import Computer
    OHM_AVAILABLE = True
except Exception:
    OHM_AVAILABLE = False


# -----------------------------
# WMI SENSOR READER
# -----------------------------
def get_wmi_temps():
    """
    Attempts to read CPU temperature using Windows WMI.
    Works on many laptops, but not all hardware exposes sensors.
    Returns temperature in °C or None.
    """
    try:
        w = wmi.WMI(namespace="root\\wmi")
        sensors = w.MSAcpi_ThermalZoneTemperature()
        if not sensors:
            return None

        # Convert tenths of Kelvin to Celsius
        temp = sensors[0].CurrentTemperature
        return round((temp / 10) - 273.15, 1)
    except Exception:
        return None


# -----------------------------
# OPENHARDWAREMONITOR SENSOR READER
# -----------------------------
def get_ohm_temps():
    """
    Reads CPU and GPU temps via OpenHardwareMonitor if available.
    Requires OHM running OR pythonnet + OHM DLL in working directory.
    Returns dict: { "cpu": float | None, "gpu": float | None }
    """
    if not OHM_AVAILABLE:
        return {"cpu": None, "gpu": None}

    try:
        comp = Computer()
        comp.CPUEnabled = True
        comp.GPUEnabled = True
        comp.Open()

        cpu_temp = None
        gpu_temp = None

        for hw in comp.Hardware:
            hw.Update()
            if hw.HardwareType == 2:  # CPU
                for sensor in hw.Sensors:
                    if sensor.SensorType == 2:  # Temperature
                        cpu_temp = round(sensor.Value, 1)
            if hw.HardwareType == 4:  # GPU
                for sensor in hw.Sensors:
                    if sensor.SensorType == 2:
                        gpu_temp = round(sensor.Value, 1)

        return {"cpu": cpu_temp, "gpu": gpu_temp}

    except Exception:
        return {"cpu": None, "gpu": None}


# -----------------------------
# DISK USAGE
# -----------------------------
def get_disk_usage():
    """
    Returns a dict of drive letters and their usage percentages.
    Example: { "C": 42.1, "D": 77.3 }
    """
    usage = {}
    for part in psutil.disk_partitions():
        if "cdrom" in part.opts or part.fstype == "":
            continue
        try:
            letter = part.device.replace("\\", "").replace(":", "")
            usage[letter] = psutil.disk_usage(part.device).percent
        except Exception:
            pass
    return usage


# -----------------------------
# MASTER SENSOR FUNCTION
# -----------------------------
def get_all_sensors():
    """
    Returns a unified dictionary of all sensor data.
    UI layer should call ONLY this function.
    """

    # CPU / RAM
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent

    # Disks
    disks = get_disk_usage()

    # Temperatures
    wmi_temp = get_wmi_temps()
    ohm_temps = get_ohm_temps()

    # Prefer OHM if available
    cpu_temp = ohm_temps.get("cpu") or wmi_temp
    gpu_temp = ohm_temps.get("gpu")

    return {
        "cpu": cpu,
        "ram": ram,
        "disks": disks,
        "temps": {
            "cpu": cpu_temp,
            "gpu": gpu_temp
        }
    }
