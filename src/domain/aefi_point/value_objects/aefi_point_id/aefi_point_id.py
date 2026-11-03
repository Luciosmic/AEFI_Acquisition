"""AefiPointId typed identity (see aefi_point_id_intention.md)."""

from typing import NewType
from uuid import UUID

AefiPointId = NewType("AefiPointId", UUID)
