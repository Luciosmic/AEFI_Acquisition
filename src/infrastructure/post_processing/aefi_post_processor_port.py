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
- The rotation angles follow the active sensor calibration
  (ActiveSensorRotationChanged), captured when the scan completes.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from PySide6.QtCore import QProcess

from application.services.scan_export_service.ports.i_post_processing_port import (
    IPostProcessingPort,
)
from application.services.sensor_calibration_service.sensor_calibration_service import (
    ACTIVE_SENSOR_ROTATION_CHANGED_TOPIC,
)
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_EXTERNAL_MODULES = _PROJECT_ROOT / "external_modules"
_COMPOSITION_ROOT = _EXTERNAL_MODULES / "aefi_post_processor_module" / "composition_root.py"

if str(_EXTERNAL_MODULES) not in sys.path:
    sys.path.insert(0, str(_EXTERNAL_MODULES))


def rotation_origin(is_trial: bool, is_calibrated: bool, recorded_at: Optional[datetime]) -> str:
    """Human-readable provenance of the active sensor rotation angles."""
    if is_trial:
        return "trial"
    if is_calibrated:
        return "calibrated " + recorded_at.isoformat()
    return "ideal default"


class AefiPostProcessorPort(IPostProcessingPort):
    """Runs the AEFI post-processing pipeline, then opens its visualizer."""

    _REFERENCE_POINT = (0, 0)

    def __init__(
        self,
        event_bus: IDomainEventBus,
        initial_rotation_angles: Tuple[float, float, float],
        initial_rotation_origin: str,
    ) -> None:
        self._rotation_angles = tuple(initial_rotation_angles)
        self._rotation_origin = initial_rotation_origin
        event_bus.subscribe(ACTIVE_SENSOR_ROTATION_CHANGED_TOPIC, self._on_active_rotation_changed)

    def _on_active_rotation_changed(self, event) -> None:
        a = event.angles
        self._rotation_angles = (a.theta_x_degrees, a.theta_y_degrees, a.theta_z_degrees)
        self._rotation_origin = rotation_origin(event.is_trial, event.is_calibrated, event.recorded_at)
        logger.debug(
            "AefiPostProcessorPort: active sensor rotation now %s (%s)",
            self._rotation_angles, self._rotation_origin,
        )

    def run(self, csv_path: Path, hdf5_path: Path) -> None:
        try:
            self._process(csv_path, hdf5_path)
        except Exception as exc:
            logger.error("Post-processing failed for %s: %s", csv_path, exc)
            return

        self._launch_visualizer(hdf5_path.parent)

    def _process(self, csv_path: Path, hdf5_path: Path) -> None:
        from aefi_post_processor_module.processing.processing_pipeline import ProcessingPipeline

        if self._rotation_origin == "trial":
            logger.warning(
                "AefiPostProcessorPort: post-processing %s with sensor rotation %s "
                "(trial: unrecorded angles, not a saved calibration)",
                csv_path, self._rotation_angles,
            )
        else:
            logger.info(
                "AefiPostProcessorPort: post-processing %s with sensor rotation %s (%s)",
                csv_path, self._rotation_angles, self._rotation_origin,
            )

        with ProcessingPipeline(output_path=hdf5_path) as pipeline:
            pipeline.run_full_pipeline(
                csv_path,
                rotation_angles=self._rotation_angles,
                reference_point=self._REFERENCE_POINT,
            )

    @staticmethod
    def _launch_visualizer(acquisition_dir: Path) -> None:
        QProcess.startDetached(
            sys.executable,
            [str(_COMPOSITION_ROOT), "--repo-path", str(acquisition_dir)],
        )
