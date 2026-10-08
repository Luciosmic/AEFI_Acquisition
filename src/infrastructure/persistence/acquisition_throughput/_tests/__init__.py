"""Factories of the DTOs shared by the acquisition throughput export tests."""

from dataclasses import replace
from datetime import datetime, timezone

from application.services.acquisition_throughput_characterization_service.acquisition_throughput_characterization_service import (
    CONTROLLER,
    EXCITATION_CUT,
)
from application.shared.acquisition_parameters.acquisition_conditions_dtos import (
    BenchPositionDTO,
    ExportedFileDTO,
)
from application.services.acquisition_throughput_characterization_service.dtos.acquisition_parameters_dtos import (
    AcquisitionParametersDTO,
    OperatorExcitationDTO,
    ThroughputActivityDTO,
)
from application.services.acquisition_throughput_characterization_service.dtos.acquisition_throughput_dtos import (
    AcquisitionThroughputRequestDTO,
)
from infrastructure.acquisition_conditions.fake.fake_acquisition_conditions_port import make_bench_conditions
from infrastructure.provenance.fake.fake_software_provenance_port import CLEAN


def make_throughput_activity_dto(**overrides) -> ThroughputActivityDTO:
    """A completed sweep on the bench (n_avg 1, 8, 127; latency 1 ms)."""
    activity = ThroughputActivityDTO(
        activity_id="act-1",
        started_at=datetime(2026, 10, 2, 12, 3, 11, tzinfo=timezone.utc),
        status="completed",
        request=AcquisitionThroughputRequestDTO(n_avg_values=(1, 8, 127), samples_per_point=50),
        settle_delay_s=0.5,
        sample_timeout_s=60.0,
        excitation_condition=EXCITATION_CUT,
        controller=CONTROLLER,
        held_controls=("excitation", "acquisition_stream", "hardware_configuration:mcu", "hardware_configuration:ads131a04"),
        operator_n_avg=127,
        operator_excitation=OperatorExcitationDTO("X_DIR", 20.0, 20.0, 1000.0),
        stream_started_here=True,
        ended_at=datetime(2026, 10, 2, 12, 9, 40, tzinfo=timezone.utc),
        n_avg_restored=True,
        excitation_restored=True,
        bench_position_start=BenchPositionDTO(12.5, -3.0),
        bench_position_end=BenchPositionDTO(12.5, -3.0),
        usb_latency_timer_ms=1.0,
    )
    return replace(activity, **overrides)


def make_acquisition_parameters_dto(**overrides) -> AcquisitionParametersDTO:
    parameters = AcquisitionParametersDTO(
        activity=make_throughput_activity_dto(),
        conditions=make_bench_conditions(),
        software=CLEAN,
        files=(
            ExportedFileDTO("summary.csv", "CSV", 1234, "a" * 64),
            ExportedFileDTO("samples.csv", "CSV", 56789, "b" * 64),
        ),
    )
    return replace(parameters, **overrides)
