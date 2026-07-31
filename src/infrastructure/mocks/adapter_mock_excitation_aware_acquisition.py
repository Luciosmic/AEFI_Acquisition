"""
Mock: Excitation-Aware Acquisition Port

Responsibility:
    - Integrates acquisition and excitation systems seamlessly
    - Applies the physically-simulated field of the 4 excitation spheres,
      as read by the 8mm cube sensor (see CubeSensorFieldSimulator), to the
      in-phase acquisition components

Rationale:
    - Simulates the physical coupling between excitation and acquisition
    - After synchronous detection, signal characteristics are tied to excitation level
    - Frequency has no impact (processing occurs after synchronous detection)
    - No object-under-test is modeled (empty-bench baseline), so
      ExcitationMode has no effect — only level_s1_s2/level_s3_s4 do

Design:
    - Wraps an IAcquisitionPort to intercept measurements
    - Observes excitation changes via IExcitationPort or direct parameter updates
    - Delegates the field computation (including sensor orientation and finite-
      size face averaging) entirely to CubeSensorFieldSimulator
"""

from typing import Optional

from application.services.scan_application_service.ports.i_acquisition_port import IAcquisitionPort
from application.services.excitation_configuration_service.ports.i_excitation_port import IExcitationPort
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement
from domain.shared_kernel.excitation.value_objects.excitation_parameters import ExcitationParameters
from infrastructure.mocks.cube_sensor_field_simulator import CubeSensorFieldSimulator


class ExcitationAwareAcquisitionPort(IAcquisitionPort):
    """
    Mock acquisition port that applies the excitation spheres' simulated
    field (as read by the cube sensor) to measurements.

    Usage:
        base_port = RandomNoiseAcquisitionPort()
        excitation_port = MockExcitationPort()
        aware_port = ExcitationAwareAcquisitionPort(base_port, excitation_port)

        excitation_port.apply_excitation(ExcitationParameters(...))
        measurement = aware_port.acquire_sample()
    """

    def __init__(
        self,
        base_acquisition_port: IAcquisitionPort,
        excitation_port: Optional[IExcitationPort] = None,
        field_simulator: Optional[CubeSensorFieldSimulator] = None,
    ):
        """
        Args:
            base_acquisition_port: Base acquisition port to wrap
            excitation_port: Optional excitation port to observe (if None, use manual updates)
            field_simulator: Optional injected simulator (defaults to loading
                .aefi_acquisition/configs/aefi_device_config.json)
        """
        self._base_port = base_acquisition_port
        self._excitation_port = excitation_port
        self._field_simulator = field_simulator or CubeSensorFieldSimulator.from_default_config()

        # Current excitation state (tracked manually if no port provided)
        self._current_excitation: Optional[ExcitationParameters] = None

    def acquire_sample(self) -> AefiVoltageMeasurement:
        """Acquire a sample and apply the simulated excitation field."""
        base_measurement = self._base_port.acquire_sample()

        excitation = self._get_current_excitation()
        if not excitation:
            return base_measurement

        ux, uy, uz = self._field_simulator.compute_axis_voltages(
            excitation.level_s1_s2.value, excitation.level_s3_s4.value
        )
        if ux == 0.0 and uy == 0.0 and uz == 0.0:
            return base_measurement

        return self._apply_offset_to_measurement(base_measurement, ux, uy, uz)

    def is_ready(self) -> bool:
        """Check if base acquisition port is ready."""
        return self._base_port.is_ready()

    def get_quantification_noise(self) -> float:
        """Get quantification noise from base port."""
        if hasattr(self._base_port, 'get_quantification_noise'):
            return self._base_port.get_quantification_noise()
        return 0.0

    def set_excitation_parameters(self, params: ExcitationParameters) -> None:
        """Manually set excitation parameters (if not using excitation port)."""
        self._current_excitation = params

    def _get_current_excitation(self) -> Optional[ExcitationParameters]:
        """Get current excitation parameters from port or manual tracking."""
        if self._excitation_port and hasattr(self._excitation_port, 'last_parameters'):
            return self._excitation_port.last_parameters
        return self._current_excitation

    @staticmethod
    def _apply_offset_to_measurement(
        measurement: AefiVoltageMeasurement,
        ux: float,
        uy: float,
        uz: float,
    ) -> AefiVoltageMeasurement:
        """
        Apply the simulated field (already in Sensor Frame — see
        CubeSensorFieldSimulator) to the in-phase components of a voltage
        measurement. Quadrature is left untouched — both DDS pairs run at
        the same frequency, so this empty-bench model has no phase shift to
        contribute.
        """
        return AefiVoltageMeasurement(
            voltage_x_in_phase=measurement.voltage_x_in_phase + ux,
            voltage_x_quadrature=measurement.voltage_x_quadrature,
            voltage_y_in_phase=measurement.voltage_y_in_phase + uy,
            voltage_y_quadrature=measurement.voltage_y_quadrature,
            voltage_z_in_phase=measurement.voltage_z_in_phase + uz,
            voltage_z_quadrature=measurement.voltage_z_quadrature,
            timestamp=measurement.timestamp,
            uncertainty_estimate_volts=measurement.uncertainty_estimate_volts,
            std_dev_x_in_phase=measurement.std_dev_x_in_phase,
            std_dev_x_quadrature=measurement.std_dev_x_quadrature,
            std_dev_y_in_phase=measurement.std_dev_y_in_phase,
            std_dev_y_quadrature=measurement.std_dev_y_quadrature,
            std_dev_z_in_phase=measurement.std_dev_z_in_phase,
            std_dev_z_quadrature=measurement.std_dev_z_quadrature,
        )
