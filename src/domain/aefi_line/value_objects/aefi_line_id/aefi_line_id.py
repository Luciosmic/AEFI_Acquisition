"""AefiLineId typed identity (see aefi_line_id_intention.md)."""

from typing import NewType
from uuid import UUID

AefiLineId = NewType("AefiLineId", UUID)
