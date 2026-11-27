"""
Fake raw increment motion port: re-export of the published Arcus package.

The code lives in arcus_performax_4ex.fake.fake_raw_increment_motion_port (Arcus-Performax-4EX repo, installed as a uv
dependency pinned to a tag). This module keeps its AEFI path so that existing
imports keep working. See fake_adapter_raw_increment_motion_arcus_intention.md.
"""

from arcus_performax_4ex.fake.fake_raw_increment_motion_port import (  # noqa: F401 — re-exported
    FakeRawIncrementMotionPort as FakeRawIncrementMotionPort,
    HOME_SWITCH_TRIP_INCREMENTS as HOME_SWITCH_TRIP_INCREMENTS,
    POSITION_REQUEST_S as POSITION_REQUEST_S,
)
