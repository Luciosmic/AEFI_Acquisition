"""Shared test factories for the persistence tests."""

from dataclasses import replace
from datetime import datetime, timezone

from application.services.scan_export_service.dtos.scan_acquisition_parameters_dtos import (
    STEP_SCAN,
    ExcitationStateDTO,
    ScanAcquisitionParametersDTO,
    ScanActivityDTO,
    StepScanProcedureDTO,
)
from application.shared.acquisition_parameters.acquisition_conditions_dtos import BenchPositionDTO
from infrastructure.acquisition_conditions.fake.fake_acquisition_conditions_port import make_bench_conditions
from infrastructure.provenance.fake.fake_software_provenance_port import CLEAN

STARTED = datetime(2026, 10, 2, 14, 0, 0, tzinfo=timezone.utc)
ENDED = datetime(2026, 10, 2, 14, 5, 0, tzinfo=timezone.utc)


def make_step_scan_procedure(**overrides) -> StepScanProcedureDTO:
    fields = dict(
        x_min_mm=435.0, x_max_mm=835.0, y_min_mm=435.0, y_max_mm=835.0, x_nb_points=21, y_nb_points=21,
        total_points=441, pattern="SERPENTINE", fast_axis="Y", stabilization_delay_ms=300.0,
        averaging_per_position=10, measurement_uncertainty_v=1e-6, differential_mode=False,
        differential_settle_delay_ms=50.0, estimated_duration_s=600.0,
    )
    fields.update(overrides)
    return StepScanProcedureDTO(**fields)


def make_scan_activity(kind: str = STEP_SCAN, **overrides) -> ScanActivityDTO:
    fields = dict(
        activity_id="scan-1", kind=kind, started_at=STARTED, status="running",
        excitation=ExcitationStateDTO(mode="X_DIR", level_s1_s2_percent=80.0, level_s3_s4_percent=60.0),
        owner="scan", held_controls=("excitation",),
        procedure=make_step_scan_procedure() if kind == STEP_SCAN else None,
        bench_position_start=BenchPositionDTO(x_mm=435.0, y_mm=435.0), usb_latency_timer_ms=1.0,
    )
    fields.update(overrides)
    return ScanActivityDTO(**fields)


def make_scan_acquisition_parameters(kind: str = STEP_SCAN, ended: bool = False, **activity) -> ScanAcquisitionParametersDTO:
    parameters = ScanAcquisitionParametersDTO(
        activity=make_scan_activity(kind, **activity), conditions=make_bench_conditions(), software=CLEAN,
    )
    if ended:
        parameters = replace(parameters, activity=replace(
            parameters.activity, ended_at=ENDED, status="completed", records_written=441,
            bench_position_end=BenchPositionDTO(x_mm=835.0, y_mm=835.0),
        ))
    return parameters
