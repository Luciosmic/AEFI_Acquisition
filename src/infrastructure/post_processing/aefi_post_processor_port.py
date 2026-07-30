"""
AEFI Post-Processor Adapter

Responsibility:
- Implement `IPostProcessingPort` by driving the
  `external_modules/aefi_post_processor_module` pipeline in-process to fill
  a scan's HDF5 file with processing steps, then spawning the module's
  visualization app as a separate OS process (a second QApplication cannot
  run inside this one).

Rationale:
- `aefi_post_processor_module` is a third-party module (see CLAUDE.md,
  "external_modules/ # modules tiers"), not part of this DDD codebase —
  this adapter is the single point of contact with it.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtCore import QProcess

from application.services.scan_export_service.ports.i_post_processing_port import (
    IPostProcessingPort,
)

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_EXTERNAL_MODULES = _PROJECT_ROOT / "external_modules"
_COMPOSITION_ROOT = _EXTERNAL_MODULES / "aefi_post_processor_module" / "composition_root.py"

if str(_EXTERNAL_MODULES) not in sys.path:
    sys.path.insert(0, str(_EXTERNAL_MODULES))


class AefiPostProcessorPort(IPostProcessingPort):
    """Runs the AEFI post-processing pipeline, then opens its visualizer."""

    # ponytail: hardcoded, matching aefi_post_processor_module's own
    # composition_root.py default — surface as scan config if a different
    # probe geometry ever needs another value.
    _ROTATION_ANGLES = (35.26, -45.00, -7.20)
    _REFERENCE_POINT = (0, 0)

    def run(self, csv_path: Path, hdf5_path: Path) -> None:
        try:
            self._process(csv_path, hdf5_path)
        except Exception as exc:
            logger.error("Post-processing failed for %s: %s", csv_path, exc)
            return

        self._launch_visualizer(hdf5_path.parent)

    def _process(self, csv_path: Path, hdf5_path: Path) -> None:
        from aefi_post_processor_module.processing.processing_pipeline import ProcessingPipeline

        with ProcessingPipeline(output_path=hdf5_path) as pipeline:
            pipeline.run_full_pipeline(
                csv_path,
                rotation_angles=self._ROTATION_ANGLES,
                reference_point=self._REFERENCE_POINT,
            )

    @staticmethod
    def _launch_visualizer(acquisition_dir: Path) -> None:
        QProcess.startDetached(
            sys.executable,
            [str(_COMPOSITION_ROOT), "--repo-path", str(acquisition_dir)],
        )
