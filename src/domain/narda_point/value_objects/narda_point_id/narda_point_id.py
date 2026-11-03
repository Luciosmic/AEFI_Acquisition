"""NardaPointId typed identity (see narda_point_id_intention.md)."""

from typing import NewType
from uuid import UUID

NardaPointId = NewType("NardaPointId", UUID)
