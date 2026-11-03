"""
AEFI Continuous Reading Presenter - Interface V2

Bridges between AefiAcquisitionService and AefiContinuousReadingPanel.
Adapted from interface v1 for PySide6.
"""

from PySide6.QtCore import QObject, Signal, Slot
from typing import Dict, Any

from application.services.aefi_acquisition_service.aefi_acquisition_service import (
    AEFI_ACQUISITION_CONTROL_CHANGED_TOPIC,
    AefiAcquisitionService,
)
from application.services.aefi_acquisition_service.ports.i_aefi_acquisition_executor import AefiAcquisitionConfig
from application.services.aefi_signal_processing_service.aefi_signal_processing_service import (
    AefiSignalProcessingService,
)
from application.services.scan_export_service.scan_export_service import ScanExportService
from application.services.scan_export_service.dtos.scan_export_dtos import ExportConfigDTO
from domain.shared_kernel.events.aefi_voltage_reading_failed.aefi_voltage_reading_failed import (
    AefiVoltageReadingFailed,
)
from domain.shared_kernel.events.aefi_voltage_reading_stopped.aefi_voltage_reading_stopped import (
    AefiVoltageReadingStopped,
)
from domain.shared_kernel.events.sensor_transformation_angles_updated.sensor_transformation_angles_updated import (
    SensorTransformationAnglesUpdated,
)
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus
from domain.signal_processing.events.aefi_corrected_field_sample_acquired.aefi_corrected_field_sample_acquired import (
    AefiCorrectedFieldSampleAcquired,
)
from domain.signal_processing.events.aefi_signal_correction_calibration_updated.aefi_signal_correction_calibration_updated import (
    AefiSignalCorrectionCalibrationUpdated,
)
from application.services.transformation_service.transformation_service import TransformationService
from interface.view_models.aefi_continuous_reading_sample_view_model import (
    AefiContinuousReadingSampleViewModel,
)

class AefiContinuousReadingPresenter(QObject):
    """
    Presenter for AefiContinuousReadingPanel.
    - Translates UI interactions to service calls
    - Subscribes to domain events and emits Qt signals
    - Delegates signal correction (Noise, Phase, Primary) to AefiSignalProcessingService
    - Delegates Coordinate Transformation to TransformationService (still used directly
      for on_rotation_toggled/angles_updated, independent of the correction pipeline)
    """

    # Signals emitted to the UI
    acquisition_started = Signal(str)   # acquisition_id
    acquisition_stopped = Signal(str)   # acquisition_id
    acquisition_failed = Signal(str)    # reason
    sample_acquired = Signal(object)    # AefiContinuousReadingSampleViewModel
    angles_updated = Signal(tuple)      # For updating the read-only display
    correction_states_updated = Signal(bool, bool, bool, str, str, str)  # (noise, phase, primary, noise_str, phase_str, primary_str)
    # (controller, running): who holds the stream ("" = free, Start/Stop by hand) and whether it runs
    acquisition_control_changed = Signal(str, bool)

    def __init__(self, service: AefiAcquisitionService, event_bus: IDomainEventBus,
                 transformation_service: TransformationService,
                 signal_processing_service: AefiSignalProcessingService,
                 export_service: ScanExportService):
        super().__init__()
        self._service = service
        self._export_service = export_service
        self._event_bus = event_bus
        self._transformation_service = transformation_service
        self._signal_processing_service = signal_processing_service
        self._current_acquisition_id: str | None = None

        # Subscribe to domain events - USE LOWERCASE EVENT NAMES (matching publish calls)
        self._event_bus.subscribe("aeficorrectedfieldsampleacquired", self._on_corrected_sample_event)
        self._event_bus.subscribe("aefisignalcorrectioncalibrationupdated", self._on_calibration_updated)
        self._event_bus.subscribe("aefivoltagereadingfailed", self._on_failed_event)
        self._event_bus.subscribe("aefivoltagereadingstopped", self._on_stopped_event)
        self._event_bus.subscribe("sensortransformationanglesupdated", self._on_angles_updated_event)
        # A scan / calibration / characterization holds the stream: lock Start/Stop, show who.
        self._event_bus.subscribe(AEFI_ACQUISITION_CONTROL_CHANGED_TOPIC, self._on_control_changed_event)

    def _on_control_changed_event(self, event) -> None:
        self.refresh_control_state()

    def refresh_control_state(self) -> None:
        self.acquisition_control_changed.emit(
            self._service.get_controller() or "", self._service.is_acquisition_running()
        )

    def _on_angles_updated_event(self, event: SensorTransformationAnglesUpdated):
        """Handle rotation angles update event."""
        self.angles_updated.emit((event.theta_x, event.theta_y, event.theta_z))

    # ------------------------------------------------------------------ #
    # Calibration Commands — pure delegation to AefiSignalProcessingService.
    # Feedback (correction_states_updated) is pushed reactively by
    # _on_calibration_updated once the service publishes its event — no
    # direct call to an "emit states" helper here.
    # ------------------------------------------------------------------ #

    @staticmethod
    def _fmt_offset(offset: dict) -> str:
        """Format {axis: (I, Q)} as compact magnitude string in mV. Keys are
        the domain's lowercase axis names ("x"/"y"/"z")."""
        import math
        parts = []
        for ax in ("x", "y", "z"):
            i, q = offset.get(ax, (0.0, 0.0))
            mag_mv = math.sqrt(i**2 + q**2) * 1000
            parts.append(f"{ax.upper()}={mag_mv:.2f}")
        return "  ".join(parts) + " mV"

    @staticmethod
    def _fmt_phase(angles: dict) -> str:
        """Format {axis: radians} as compact degree string. Keys are the
        domain's lowercase axis names ("x"/"y"/"z")."""
        import math
        parts = []
        for ax in ("x", "y", "z"):
            deg = math.degrees(angles.get(ax, 0.0))
            parts.append(f"{ax.upper()}={deg:.1f}°")
        return "  ".join(parts)

    def _on_calibration_updated(self, event: AefiSignalCorrectionCalibrationUpdated) -> None:
        """Reformat the calibration snapshot pushed by AefiSignalProcessingService
        (a calibrate_* command, an enable/disable toggle, or a reset) for display."""
        calibration = event.calibration
        noise_str = self._fmt_offset(calibration.noise_offset) if calibration.noise_offset else "—"
        phase_str = self._fmt_phase(calibration.phase_angles) if calibration.phase_angles else "—"
        primary_str = self._fmt_offset(calibration.primary_offset) if calibration.primary_offset else "—"
        self.correction_states_updated.emit(
            calibration.noise_correction_enabled,
            calibration.phase_correction_enabled,
            calibration.primary_correction_enabled,
            noise_str,
            phase_str,
            primary_str,
        )

    @Slot()
    def calibrate_noise(self):
        """Use last received sample to calibrate noise offset."""
        self._signal_processing_service.calibrate_noise()

    @Slot()
    def calibrate_phase(self):
        """Use last received sample (after noise correction) to align phase."""
        self._signal_processing_service.calibrate_phase()

    @Slot()
    def calibrate_primary(self):
        """Use last received (fully processed) sample to tare primary field."""
        self._signal_processing_service.calibrate_primary()

    @Slot()
    def reset_calibration(self):
        """Clear all offsets and corrections."""
        self._signal_processing_service.reset_calibration()

    @Slot(bool)
    def on_noise_toggled(self, enabled: bool):
        self._signal_processing_service.set_noise_correction_enabled(enabled)

    @Slot(bool)
    def on_phase_toggled(self, enabled: bool):
        self._signal_processing_service.set_phase_correction_enabled(enabled)

    @Slot(bool)
    def on_primary_toggled(self, enabled: bool):
        self._signal_processing_service.set_primary_correction_enabled(enabled)

    # ------------------------------------------------------------------ #
    # UI Commands (from panel signals)
    # ------------------------------------------------------------------ #

    @Slot(dict)
    def on_acquisition_start_requested(self, params: Dict[str, Any]):
        """
        Handle start request from panel.

        Args:
            params: {max_duration_s (optional), export_enabled, export_filename_base,
                     measured_object, operator_id, operator}
        """
        # Always (re)configured, so an unchecked box disarms a previous arming.
        self._export_service.configure_time_series_export(ExportConfigDTO(
            enabled=bool(params.get("export_enabled", False)),
            output_directory="",  # default exports dir, same as the scan panel's empty field
            filename_base=params.get("export_filename_base") or "continuous",
            measured_object=params.get("measured_object", ""),
            operator_id=params.get("operator_id", ""),
            operator=params.get("operator", ""),
        ))
        config = AefiAcquisitionConfig(
            max_duration_s=params.get("max_duration_s", None),
            target_uncertainty=None,
        )
        result = self._service.start_acquisition(config)
        if result.is_failure:
            self.acquisition_failed.emit(f"Démarrage refusé : {result.error}")
            self.refresh_control_state()

    @Slot()
    def on_acquisition_stop_requested(self):
        """Handle stop request from panel."""
        result = self._service.stop_acquisition()
        if result.is_failure:
            self.acquisition_failed.emit(f"Arrêt refusé : {result.error}")
            self.refresh_control_state()
            return
        if self._current_acquisition_id is not None:
            self.acquisition_stopped.emit(self._current_acquisition_id)

    @Slot(bool)
    def on_rotation_toggled(self, enabled: bool):
        """Enable/Disable rotation in the service."""
        self._transformation_service.set_enabled(enabled)
        # Also update the read-only display with current angles
        self.angles_updated.emit(self._transformation_service.get_rotation_angles())

    # ... (UI Commands remain same) ...



    def _on_failed_event(self, event: AefiVoltageReadingFailed):
        """Handle acquisition failure."""
        self.acquisition_failed.emit(str(event.reason))

    def _on_stopped_event(self, event: AefiVoltageReadingStopped):
        """Handle acquisition stop."""
        if self._current_acquisition_id is not None:
            self.acquisition_stopped.emit(str(event.acquisition_id))
            self._current_acquisition_id = None

    def _on_corrected_sample_event(self, event: AefiCorrectedFieldSampleAcquired):
        """
        Handle a corrected field sample event (already corrected + transformed
        sensor -> source by AefiSignalProcessingService) — build the view model
        and emit it. No correction or transformation logic here anymore.
        Called from the executor thread — emit Qt signals for UI thread.
        """
        acquisition_id_str = str(event.acquisition_id)

        if self._current_acquisition_id is None:
            self._current_acquisition_id = acquisition_id_str
            self.acquisition_started.emit(acquisition_id_str)

        m = event.sample
        view_model = AefiContinuousReadingSampleViewModel(
            acquisition_id=acquisition_id_str,
            sample_index=event.sample_index,
            timestamp_iso=m.timestamp.isoformat(),
            ux_in_phase=m.field_x_in_phase,
            ux_quadrature=m.field_x_quadrature,
            uy_in_phase=m.field_y_in_phase,
            uy_quadrature=m.field_y_quadrature,
            uz_in_phase=m.field_z_in_phase,
            uz_quadrature=m.field_z_quadrature,
        )

        self.sample_acquired.emit(view_model)


    def shutdown(self):
        """Cleanup resources."""
        # Unsubscribe from events — keys must match the lowercase topics used
        # by subscribe() (InMemoryEventBus keys are exact string matches).
        if self._event_bus:
            self._event_bus.unsubscribe("aeficorrectedfieldsampleacquired", self._on_corrected_sample_event)
            self._event_bus.unsubscribe("aefisignalcorrectioncalibrationupdated", self._on_calibration_updated)
            self._event_bus.unsubscribe("aefivoltagereadingfailed", self._on_failed_event)
            self._event_bus.unsubscribe("aefivoltagereadingstopped", self._on_stopped_event)
            self._event_bus.unsubscribe("sensortransformationanglesupdated", self._on_angles_updated_event)
