"""Hardware capability detection for rendering fallbacks.

Certain subsets of legacy Windows hardware trigger a DWM recomposition
loop when the HUD's translucent, painter-rendered surface is refreshed on
the GUI thread. Rather than forcing hardware acceleration off everywhere,
we only degrade the renderer when the machine clearly falls below a
generation threshold.
"""

from __future__ import annotations

import logging

import psutil

logger = logging.getLogger(__name__)

# A legacy profile: few logical cores plus modest physical memory. These
# thresholds are intentionally conservative so modern machines keep
# hardware-accelerated rendering and only clearly dated hardware falls back.
LOW_CORE_THRESHOLD = 4
LOW_RAM_THRESHOLD_BYTES = 8 * 1024**3  # 8 GiB


def _logical_cores() -> int | None:
    try:
        count = psutil.cpu_count(logical=True)
        return count if count else None
    except (OSError, RuntimeError):
        return None


def _total_memory() -> int | None:
    try:
        return int(psutil.virtual_memory().total)
    except (OSError, RuntimeError):
        return None


def is_low_spec() -> bool:
    """Return True when the host is likely GPU-limited legacy hardware."""
    cores = _logical_cores()
    memory = _total_memory()
    low_cores = cores is not None and cores <= LOW_CORE_THRESHOLD
    low_memory = memory is not None and memory <= LOW_RAM_THRESHOLD_BYTES
    if low_cores and low_memory:
        logger.debug(
            "Low-spec profile detected (cores=%s, ram=%s GiB); disabling hardware acceleration",
            cores,
            None if memory is None else round(memory / 1024**3, 1),
        )
        return True
    logger.debug("Rendering profile: cores=%s, ram=%s", cores, memory)
    return False
