"""ScanId typed identity (see scan_id_intention.md)."""

from typing import NewType
from uuid import UUID

ScanId = NewType("ScanId", UUID)
