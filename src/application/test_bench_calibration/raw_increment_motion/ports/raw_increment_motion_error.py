"""
Raw Increment Motion Error: re-export of the published Arcus package.

The code lives in arcus_performax_4ex.ports.raw_increment_motion_error (Arcus-Performax-4EX repo, installed as a uv
dependency pinned to a tag). This module keeps its AEFI path so that existing
imports keep working. See raw_increment_motion_error_intention.md.
"""

from arcus_performax_4ex.ports.raw_increment_motion_error import (  # noqa: F401 — re-exported
    RawIncrementMotionError as RawIncrementMotionError,
)
