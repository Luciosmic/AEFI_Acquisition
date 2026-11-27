"""
Arcus Performax 4EX controller: re-export of the published Arcus package.

The code lives in arcus_performax_4ex.driver_arcus_performax4ex (Arcus-Performax-4EX repo, installed as a uv
dependency pinned to a tag). This module keeps its AEFI path so that existing
imports keep working. See driver_arcus_performax4ex_intention.md.
"""

from arcus_performax_4ex.driver_arcus_performax4ex import (  # noqa: F401 — re-exported
    ArcusPerformax4EXController as ArcusPerformax4EXController,
    AxisParams as AxisParams,
)
