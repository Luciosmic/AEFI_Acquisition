"""
Raw Increment Motion Port Interface: re-export of the published Arcus package.

The code lives in arcus_performax_4ex.ports.i_raw_increment_motion_port (Arcus-Performax-4EX repo, installed as a uv
dependency pinned to a tag). This module keeps its AEFI path so that existing
imports keep working. See i_raw_increment_motion_port_intention.md.
"""

from arcus_performax_4ex.ports.i_raw_increment_motion_port import (  # noqa: F401 — re-exported
    IRawIncrementMotionPort as IRawIncrementMotionPort,
)
