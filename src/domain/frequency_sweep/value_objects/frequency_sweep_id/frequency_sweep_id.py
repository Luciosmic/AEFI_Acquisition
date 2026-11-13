"""FrequencySweepId typed identity (see frequency_sweep_id_intention.md)."""

from typing import NewType
from uuid import UUID

FrequencySweepId = NewType("FrequencySweepId", UUID)
