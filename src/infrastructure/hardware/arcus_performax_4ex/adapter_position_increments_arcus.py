"""
Arcus Position Increments Adapter

See i_position_increments_port.py (application/scan/scan_export_service/ports).
"""

import logging
from typing import Optional, Tuple

from application.scan.scan_export_service.ports.i_position_increments_port import IPositionIncrementsPort
from infrastructure.hardware.arcus_performax_4ex.adapter_motion_port_arcus_performax4ex import ArcusAdapter

logger = logging.getLogger(__name__)


class ArcusPositionIncrementsAdapter(IPositionIncrementsPort):
    """Reads the commanded and reported increments from the motion adapter, which owns the conversion."""

    def __init__(self, motion: ArcusAdapter) -> None:
        self._motion = motion

    def increments_of(self, x_mm: float, y_mm: float) -> Optional[Tuple[int, int]]:
        if not self._motion.is_conversion_available():
            return None
        return self._motion.mm_to_increments(x_mm, y_mm)

    def read_increments(self) -> Optional[Tuple[int, int]]:
        try:
            return self._motion.read_increments()
        except Exception as error:  # controller not connected / not answering: empty cells, not a failed scan
            logger.warning("ArcusPositionIncrementsAdapter: increments unreadable: %s: %s", type(error).__name__, error)
            return None
