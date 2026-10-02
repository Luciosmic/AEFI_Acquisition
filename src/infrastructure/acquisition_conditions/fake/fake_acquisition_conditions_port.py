"""
Fake Acquisition Conditions Port

See fake_acquisition_conditions_port_intention.md.
"""

from datetime import datetime, timezone
from typing import List, Optional

from application.services.acquisition_throughput_characterization_service.dtos.acquisition_parameters_dtos import (
    AcquisitionConditionsDTO,
    AdcSettingsDTO,
    BenchPositionDTO,
    DdsChannelSettingsDTO,
    HostLinkDTO,
    MountedComponentDTO,
    SensorDeploymentDTO,
    SignalGenerationSettingsDTO,
    SynchronousDetectionStateDTO,
)
from application.services.acquisition_throughput_characterization_service.ports.i_acquisition_conditions_port import (
    IAcquisitionConditionsPort,
)
from domain.shared_kernel.operation_result import OperationResult

_RECORDED_AT = datetime(2026, 9, 30, 8, 0, tzinfo=timezone.utc)


def make_bench_conditions() -> AcquisitionConditionsDTO:
    """A plausible bench: every kind mounted (ADC noise not characterized),
    ADC at OSR 4096, AD9106 cut (DDS1/DDS2 gain 0, DDS3/DDS4 at 10000),
    sensor at the ideal angles, MCU on COM10."""
    components = (
        MountedComponentDTO("sensor", "capteur cube 8 mm", "e-sensor", _RECORDED_AT,
                            {"transduction_gain_v_per_v_per_m": 0.012}, {"transduction_gain_v_per_v_per_m": "V/(V/m)"}),
        MountedComponentDTO("conditioning_electronics_board", "carte conditionnement v2", "e-cond", _RECORDED_AT,
                            {"gain": 100.0, "bandwidth_hz": 50000.0, "noise_density_v_per_sqrt_hz": 2e-8},
                            {"gain": "V/V", "bandwidth_hz": "Hz", "noise_density_v_per_sqrt_hz": "V/√Hz"}),
        MountedComponentDTO("excitation_electronics_board", "carte excitation v1", "e-exc", _RECORDED_AT,
                            {"gain": 10.0, "bandwidth_hz": 20000.0}, {"gain": "V/V", "bandwidth_hz": "Hz"}),
        MountedComponentDTO("signal_generation_chip", "AD9106", "e-dds", _RECORDED_AT,
                            {"gain_value_per_v": 5500.0, "saturation_v": 1.0, "bandwidth_hz": 1e6},
                            {"gain_value_per_v": "value/V", "saturation_v": "V", "bandwidth_hz": "Hz"}),
        MountedComponentDTO("adc", "ADS131A04", "e-adc", _RECORDED_AT,
                            {"full_scale_v": 2.442, "lsb_v": 2.9e-7, "noise_v_rms": None, "max_sampling_rate_hz": 128000.0},
                            {"full_scale_v": "V", "lsb_v": "V/LSB", "noise_v_rms": "V RMS", "max_sampling_rate_hz": "Hz"}),
        MountedComponentDTO("microcontroller", "MCU AEFI", "e-mcu", _RECORDED_AT,
                            {"max_acquisition_rate_per_s": 130.0,
                             "optimal_acquisition_rate_per_s": ((1, 130.0), (8, 110.0), (127, 30.0))},
                            {"max_acquisition_rate_per_s": "mesures/s", "optimal_acquisition_rate_per_s": "mesures/s"},
                            {"optimal_acquisition_rate_per_s": "n_avg"}),
        MountedComponentDTO("motors", "Arcus Performax 4EX", "e-mot", _RECORDED_AT,
                            {"step_um": 21.8, "max_speed_mm_per_s": 20.0, "acceleration_mm_per_s2": 100.0},
                            {"step_um": "µm/pas", "max_speed_mm_per_s": "mm/s", "acceleration_mm_per_s2": "mm/s²"}),
    )
    return AcquisitionConditionsDTO(
        components=components,
        adc=AdcSettingsDTO(
            oversampling_ratio=4096, clkin_divider=2, iclk_divider=2, reference_voltage_v=2.442,
            reference_source="Internal", high_resolution=True, negative_charge_pump=False,
            channel_gains={str(ch): 1 for ch in range(1, 9)}, channel_enabled={str(ch): True for ch in range(1, 9)},
        ),
        signal_generation=SignalGenerationSettingsDTO(
            frequency_hz=1000.0,
            channels={
                "1": DdsChannelSettingsDTO(gain_code=0, phase_code=0, offset_code=0, constant_code=0, mode="AC"),
                "2": DdsChannelSettingsDTO(gain_code=0, phase_code=32768, offset_code=0, constant_code=0, mode="AC"),
                "3": DdsChannelSettingsDTO(gain_code=10000, phase_code=16384, offset_code=0, constant_code=0, mode="AC"),
                "4": DdsChannelSettingsDTO(gain_code=10000, phase_code=0, offset_code=0, constant_code=0, mode="AC"),
            },
            link_dds1_dds2=True, enforce_dds3_dds4_quadrature=True, link_dds3_dds4_gain=True,
        ),
        synchronous_detection=SynchronousDetectionStateDTO(compensation_enabled=False),
        sensor_deployment=SensorDeploymentDTO(
            mounting_id="m-sensor", mounted_at=_RECORDED_AT, theta_x_degrees=0.0, theta_y_degrees=-35.26,
            theta_z_degrees=45.0, rotation_origin="ideal",
        ),
        host_link=HostLinkDTO(serial_port="COM10", baud_rate=1500000),
        hardware_backends={"motion": "real", "aefi_device": "real", "electric_field_probe": "real"},
    )


class FakeAcquisitionConditionsPort(IAcquisitionConditionsPort):
    """Returns the given conditions (default: `make_bench_conditions()`);
    `positions` are returned in turn by read_bench_position (the last one
    repeats); `position_failure` reproduces disconnected motors."""

    def __init__(
        self,
        conditions: Optional[AcquisitionConditionsDTO] = None,
        positions: Optional[List[BenchPositionDTO]] = None,
        position_failure: Optional[str] = None,
    ) -> None:
        self._conditions = conditions if conditions is not None else make_bench_conditions()
        self._positions = list(positions) if positions else [BenchPositionDTO(x_mm=0.0, y_mm=0.0)]
        self._position_failure = position_failure
        self.conditions_reads = 0

    def read_conditions(self) -> AcquisitionConditionsDTO:
        self.conditions_reads += 1
        return self._conditions

    def read_bench_position(self) -> OperationResult[BenchPositionDTO, str]:
        if self._position_failure is not None:
            return OperationResult.fail(self._position_failure)
        position = self._positions.pop(0) if len(self._positions) > 1 else self._positions[0]
        return OperationResult.ok(position)
