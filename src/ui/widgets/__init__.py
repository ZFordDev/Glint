from .base import BaseWidget
from .metrics import CpuWidget, DiskWidget, GpuTempWidget, GpuUsageWidget, NetworkWidget, RamWidget

WIDGET_TYPES = {
    "cpu": CpuWidget,
    "ram": RamWidget,
    "disk": DiskWidget,
    "gpu_temp": GpuTempWidget,
    "gpu_usage": GpuUsageWidget,
    "network": NetworkWidget,
}

__all__ = ["WIDGET_TYPES", "BaseWidget"]
