"""
Post-processing service — the five processing steps of a scan (see post_processing_service_intention.md).
"""

import logging
import os
from typing import Dict, List, Optional

from ...domain.processing.amplitude_subtractor.amplitude_subtractor import PrimaryFieldAmplitudeSubtractor
from ...domain.processing.frame_rotator.frame_rotator import SensorToEFSourcesFrameRotator
from ...domain.processing.grid_builder.grid_builder import GridOrigin, build_scan_grid
from ...domain.processing.interpolator.interpolator import DataInterpolator
from ...domain.processing.phase_calibrator.phase_calibrator import PrimaryFieldPhaseCalibrator
from ...domain.processing.processing_steps.processing_steps import (
    AMPLITUDE_SUBTRACTED,
    INTERPOLATED,
    PHASE_CALIBRATED,
    PREPROCESSED,
    ROTATED_FRAME,
)
from .dtos.process_scan_dto import ProcessScanDTO
from .dtos.processing_summary_dto import ProcessingSummaryDTO
from .i_api_post_processing_service import IApiPostProcessingService
from .no_scan_plan_reader import NO_SCAN_PLAN
from .ports.i_csv_scan_reader import ICsvScanReader
from .ports.i_scan_plan_reader import IScanPlanReader
from .ports.i_step_writer import IStepWriter

logger = logging.getLogger(__name__)


class PostProcessingService(IApiPostProcessingService):
    def __init__(
        self,
        csv_reader: ICsvScanReader,
        step_writer: IStepWriter,
        scan_plan_reader: IScanPlanReader = NO_SCAN_PLAN,
    ):
        self._csv_reader = csv_reader
        self._step_writer = step_writer
        self._scan_plan_reader = scan_plan_reader  # NO_SCAN_PLAN: no description is read, every scan gets the square grid

    @staticmethod
    def _rotation_angles(request: ProcessScanDTO):
        """The angles the frame is rotated by and where they come from: the acquisition's own, else the requested ones."""
        if request.applied_rotation_angles is not None:
            return tuple(request.applied_rotation_angles), 'acquisition_parameters'
        if request.parameters.rotation_angles is not None:
            return request.parameters.rotation_angles, 'request'
        return None, 'none'

    def process_scan(self, request: ProcessScanDTO) -> ProcessingSummaryDTO:
        params = request.parameters
        rotation_angles, rotation_source = self._rotation_angles(request)
        reference_point = params.reference_point
        scan = os.path.splitext(os.path.basename(request.acquisition_file))[0]
        completed: List[str] = []
        step = 'load_csv'
        logger.info(
            "pipeline.started scan=%s csv=%s rotation_angles_deg=%s reference_point=%s interpolation=%s",
            scan, request.csv_path, rotation_angles, reference_point, not request.skip_interpolation,
        )
        logger.info("pipeline.rotation_source scan=%s source=%s angles_deg=%s", scan, rotation_source, rotation_angles)

        try:
            logger.debug("pipeline.step scan=%s step=%s", scan, step)
            samples = self._csv_reader.read(request.csv_path)
            self._step_writer.record_source(request.csv_path)
            completed.append('load_csv')

            step = 'preprocess'
            logger.debug("pipeline.step scan=%s step=%s", scan, step)
            planned = self._scan_plan_reader.planned_grid(request.csv_path)
            preprocessed, metadata, origin = build_scan_grid(
                samples.x, samples.y, samples.values, samples.channel_names, planned
            )
            if origin is GridOrigin.POINTS_OFF_PLAN:
                logger.warning(
                    "pipeline.grid scan=%s origin=%s shape=%s reason=a measured point lies outside the planned grid "
                    "planned_x_points=%s planned_y_points=%s",
                    scan, origin.value, preprocessed.shape[:2], planned.x.points, planned.y.points,
                )
            else:
                logger.info("pipeline.grid scan=%s origin=%s shape=%s", scan, origin.value, preprocessed.shape[:2])
            self._step_writer.save_step(PREPROCESSED, preprocessed, metadata)
            completed.append('preprocess')

            step = 'phase_calibration'
            logger.debug("pipeline.step scan=%s step=%s reference_point=%s", scan, step, reference_point)
            phase_calibrator = PrimaryFieldPhaseCalibrator(border_width=params.border_width)
            phase_calibrated, phase_angles = phase_calibrator.calibrate(preprocessed, reference_idx=reference_point)
            phase_metadata = {'phase_angles': phase_angles, 'reference_point': reference_point}
            self._step_writer.save_step(PHASE_CALIBRATED, phase_calibrated, phase_metadata)
            completed.append('phase_calibration')

            step = 'amplitude_subtraction'
            logger.debug("pipeline.step scan=%s step=%s reference_point=%s", scan, step, reference_point)
            amplitude_subtractor = PrimaryFieldAmplitudeSubtractor(border_width=params.border_width)
            amplitude_subtracted, mean_amplitudes = amplitude_subtractor.subtract_primary_field(
                phase_calibrated, reference_idx=reference_point
            )
            amp_metadata = {'mean_amplitudes': mean_amplitudes.tolist()}
            self._step_writer.save_step(AMPLITUDE_SUBTRACTED, amplitude_subtracted, amp_metadata)
            completed.append('amplitude_subtraction')

            if rotation_angles is not None:
                step = 'frame_rotation'
                logger.debug("pipeline.step scan=%s step=%s rotation_angles_deg=%s", scan, step, rotation_angles)
                rotated, rot_metadata = SensorToEFSourcesFrameRotator().rotate(amplitude_subtracted, rotation_angles)
                self._step_writer.save_step(ROTATED_FRAME, rotated, rot_metadata)
                completed.append('frame_rotation')
            else:
                logger.warning("pipeline.frame_rotation_skipped scan=%s reason=no_rotation_angles", scan)
                rotated = amplitude_subtracted

            if not request.skip_interpolation:
                step = 'interpolation'
                logger.debug("pipeline.step scan=%s step=%s", scan, step)
                interpolator = DataInterpolator(
                    target_grid_size=params.target_grid_size,
                    interpolation_method=params.interpolation_method,
                )
                interpolated, interp_metadata = interpolator.interpolate(rotated, metadata['extent'])
                if rotation_angles is not None:
                    interp_metadata['rotation_angles'] = rotation_angles
                self._step_writer.save_step(INTERPOLATED, interpolated, interp_metadata)
                completed.append('interpolation')
            else:
                logger.info("pipeline.interpolation_skipped scan=%s reason=requested", scan)

            logger.info("pipeline.finished scan=%s steps=%s output=%s", scan, completed, request.acquisition_file)
            return ProcessingSummaryDTO(
                steps_completed=tuple(completed),
                errors=(),
                success=True,
                output_file=str(request.acquisition_file),
                processing_history=tuple(self._step_writer.processing_history()),
            )
        except Exception as e:
            logger.error("pipeline.failed scan=%s step=%s error_type=%s error=%s", scan, step, type(e).__name__, e)
            e.processing_step = step  # the caller reads which step failed without the exception changing type
            raise
