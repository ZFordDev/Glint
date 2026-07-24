import psutil

def get_cpu_usage():
    """
    Returns CPU usage percentage.
    """
    try:
        return psutil.cpu_percent()
    except Exception:
        return None


def get_ram_usage():
    """
    Returns RAM usage percentage.
    """
    try:
        return psutil.virtual_memory().percent
    except Exception:
        return None


def get_disk_usage():
    """
    Returns a dict of drive letters and their usage percentages.
    Example: { "C": 42.1, "D": 77.3 }
    """
    usage = {}
    try:
        for part in psutil.disk_partitions():
            # Skip CD-ROMs and unformatted partitions
            if "cdrom" in part.opts or part.fstype == "":
                continue

            try:
                letter = part.device.replace("\\", "").replace(":", "")
                usage[letter] = psutil.disk_usage(part.device).percent
            except Exception:
                pass
    except Exception:
        pass

    return usage


def get_network_usage():
    """
    Returns network I/O stats since boot.
    Useful for future HUD expansions.
    """
    try:
        io = psutil.net_io_counters()
        return {
            "sent": io.bytes_sent,
            "recv": io.bytes_recv
        }
    except Exception:
        return {"sent": None, "recv": None}


def get_basic_stats():
    """
    Returns a unified dictionary of basic system stats.
    This is the safe, always-available fallback layer.
    """
    return {
        "cpu": get_cpu_usage(),
        "ram": get_ram_usage(),
        "disks": get_disk_usage(),
        "network": get_network_usage()
    }
