"""
Arcus raw increment motion adapter: re-export of the published Arcus package.

The code lives in arcus_performax_4ex.adapter_raw_increment_motion_arcus (Arcus-Performax-4EX repo, installed as a uv
dependency pinned to a tag). This module keeps its AEFI path so that existing
imports keep working. See adapter_raw_increment_motion_arcus_intention.md.
"""

from arcus_performax_4ex.adapter_raw_increment_motion_arcus import (  # noqa: F401 — re-exported
    ArcusRawIncrementMotionAdapter as ArcusRawIncrementMotionAdapter,
)
