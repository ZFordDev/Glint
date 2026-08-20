"""Compatibility wrapper for integrations using the pre-1.0 stats API."""

from src.core.sensors import get_all_sensors


def get_basic_stats():
    return get_all_sensors()
