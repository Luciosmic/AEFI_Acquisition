"""
Fake Arcus Performax 4EX controller: re-export of the published Arcus package.

The code lives in arcus_performax_4ex.fake.fake_arcus_performax4ex_controller (Arcus-Performax-4EX repo, installed as a uv
dependency pinned to a tag). This module keeps its AEFI path so that existing
imports keep working. See fake_arcus_performax_4ex_intention.md.
"""

from arcus_performax_4ex.fake.fake_arcus_performax4ex_controller import (  # noqa: F401 — re-exported
    FAKE_PLUS_LIMIT_INCREMENTS as FAKE_PLUS_LIMIT_INCREMENTS,
    FakeArcusPerformax4EXController as FakeArcusPerformax4EXController,
    _MEASURED_TIMING_BY_HS as _MEASURED_TIMING_BY_HS,
)
