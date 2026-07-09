"""
Continuous Acquisition Presenter - Interface V2

Bridges between ContinuousAcquisitionService and ContinuousAcquisitionPanel.
Adapted from interface v1 for PySide6.
"""

from PySide6.QtCore import QObject, Signal, Slot
from typing import Dict, Any

from application.services.continuous_acquisition_service.continuous_acquisition_service import ContinuousAcquisitionService
from application.services.continuous_acquisition_service.i_continuous_acquisition_executor import ContinuousAcquisitionConfig
from domain.events.continuous_acquisition_events import (
    ContinuousAcquisitionSampleAcquired,
    ContinuousAcquisitionFailed,
    ContinuousAcquisitionStopped
)
from domain.events.transformation_events import SensorTransformationAnglesUpdated
from domain.events.i_domain_event_bus import IDomainEventBus
from application.services.transformation_service.transformation_service import TransformationService
from interface.presenters.signal_processor import SignalPostProcessor

class ContinuousAcquisitionPresenter(QObject):
    """
    Presenter for Continuous Acquisition Panel.
    - Translates UI interactions to service calls
    - Subscribes to domain events and emits Qt signals
    - Handles post-processing (Noise, Phase, Primary) via SignalPostProcessor
    - Handles Coordinate Transformation via TransformationService
    """

    # Signals emitted to the UI
    acquisition_started = Signal(str)   # acquisition_id
    acquisition_stopped = Signal(str)   # acquisition_id
    acquisition_failed = Signal(str)    # reason
    sample_acquired = Signal(dict)      # {acquisition_id, index, measurement:{...}, timestamp}
    angles_updated = Signal(tuple)      # For updating the read-only display
    correction_states_updated = Signal(bool, bool, bool, str, str, str)  # (noise, phase, primary, noise_str, phase_str, primary_str)

    def __init__(self, service: ContinuousAcquisitionService, event_bus: IDomainEventBus, transformation_service: TransformationService):
        super().__init__()
        self._service = service
        self._event_bus = event_bus
        self._transformation_service = transformation_service
        self._current_acquisition_id: str | None = None
        
        # Signal Processor
        self._processor = SignalPostProcessor()
        self._last_raw_sample: Dict[str, float] = {}

        # Subscribe to domain events - USE LOWERCASE EVENT NAMES (matching publish calls)
        self._event_bus.subscribe("continuousacquisitionsampleacquired", self._on_sample_event)
        self._event_bus.subscribe("continuousacquisitionfailed", self._on_failed_event)
        self._event_bus.subscribe("continuousacquisitionstopped", self._on_stopped_event)
        self._event_bus.subscribe("sensortransformationanglesupdated", self._on_angles_updated_event)

    def _on_angles_updated_event(self, event: SensorTransformationAnglesUpdated):
        """Handle rotation angles update event."""
        self.angles_updated.emit((event.theta_x, event.theta_y, event.theta_z))


    def shutdown(self):
        """Cleanup resources."""
        # Unsubscribe from events
        if self._event_bus:
            self._event_bus.unsubscribe("ContinuousAcquisitionSampleAcquired", self._on_sample_event)
            self._event_bus.unsubscribe("ContinuousAcquisitionFailed", self._on_failed_event)
            self._event_bus.unsubscribe("ContinuousAcquisitionStopped", self._on_stopped_event)
            self._event_bus.unsubscribe("SensorTransformationAnglesUpdated", self._on_angles_updated_event)
    # Calibration Commands (Logic)
    # ------------------------------------------------------------------ #
    
    @staticmethod
    def _fmt_offset(offset: dict) -> str:
        """Format {axis: (I, Q)} as compact magnitude string in mV."""
        import math
        parts = []
        for ax in ("Ux", "Uy", "Uz"):
            i, q = offset.get(ax, (0.0, 0.0))
            mag_mv = math.sqrt(i**2 + q**2) * 1000
            parts.append(f"{ax[1]}={mag_mv:.2f}")
        return "  ".join(parts) + " mV"

    @staticmethod
    def _fmt_phase(angles: dict) -> str:
        """Format {axis: radians} as compact degree string."""
        import math
        parts = []
        for ax in ("Ux", "Uy", "Uz"):
            deg = math.degrees(angles.get(ax, 0.0))
            parts.append(f"{ax[1]}={deg:.1f}°")
        return "  ".join(parts)

    def _emit_correction_states(self):
        s = self._processor.state
        noise_str = self._fmt_offset(s.noise_offset) if s.noise_offset else "—"
        phase_str = self._fmt_phase(s.phase_angles) if s.phase_angles else "—"
        primary_str = self._fmt_offset(s.primary_offset) if s.primary_offset else "—"
        self.correction_states_updated.emit(
            s.noise_correction_enabled,
            s.phase_correction_enabled,
            s.primary_correction_enabled,
            noise_str,
            phase_str,
            primary_str,
        )

    @Slot()
    def calibrate_noise(self):
        """Use last received sample to calibrate noise offset."""
        if self._last_raw_sample:
            self._processor.calibrate_noise(self._last_raw_sample)
            self._emit_correction_states()

    @Slot()
    def calibrate_phase(self):
        """Use last received sample (after noise correction) to align phase."""
        if self._last_raw_sample:
            self._processor.state.phase_correction_enabled = False
            pre_phase_sample = self._processor.process_sample(self._last_raw_sample)
            self._processor.calibrate_phase(pre_phase_sample)
            self._emit_correction_states()

    @Slot()
    def calibrate_primary(self):
        """Use last received (fully processed) sample to tare primary field."""
        if self._last_raw_sample:
            processed = self._processor.process_sample(self._last_raw_sample)
            self._processor.calibrate_primary(processed)
            self._emit_correction_states()

    @Slot()
    def reset_calibration(self):
        """Clear all offsets and corrections."""
        self._processor.reset_calibration()
        self._emit_correction_states()

    @Slot(bool)
    def on_noise_toggled(self, enabled: bool):
        self._processor.state.noise_correction_enabled = enabled

    @Slot(bool)
    def on_phase_toggled(self, enabled: bool):
        self._processor.state.phase_correction_enabled = enabled

    @Slot(bool)
    def on_primary_toggled(self, enabled: bool):
        self._processor.state.primary_correction_enabled = enabled

    # ------------------------------------------------------------------ #
    # UI Commands (from panel signals)
    # ------------------------------------------------------------------ #

    @Slot(dict)
    def on_acquisition_start_requested(self, params: Dict[str, Any]):
        """
        Handle start request from panel.
        
        Args:
            params: {sample_rate_hz, max_duration_s (optional)}
        """
        config = ContinuousAcquisitionConfig(
            sample_rate_hz=float(params.get("sample_rate_hz", 20.0)),
            max_duration_s=params.get("max_duration_s", None),
            target_uncertainty=None,
        )
        self._service.start_acquisition(config)

    @Slot()
    def on_acquisition_stop_requested(self):
        """Handle stop request from panel."""
        self._service.stop_acquisition()
        if self._current_acquisition_id is not None:
            self.acquisition_stopped.emit(self._current_acquisition_id)

    @Slot(dict)
    def on_parameters_updated(self, params: Dict[str, Any]):
        """Handle live parameter updates from panel."""
        config = ContinuousAcquisitionConfig(
            sample_rate_hz=float(params.get("sample_rate_hz", 20.0)),
            max_duration_s=params.get("max_duration_s", None),
            target_uncertainty=None,
        )
        self._service.update_acquisition_parameters(config)
    
    @Slot(bool)
    def on_rotation_toggled(self, enabled: bool):
        """Enable/Disable rotation in the service."""
        self._transformation_service.set_enabled(enabled)
        # Also update the read-only display with current angles
        self.angles_updated.emit(self._transformation_service.get_rotation_angles())

    # ... (UI Commands remain same) ...


    
    def _on_failed_event(self, event: ContinuousAcquisitionFailed):
        """Handle acquisition failure."""
        self.acquisition_failed.emit(str(event.reason))

    def _on_stopped_event(self, event: ContinuousAcquisitionStopped):
        """Handle acquisition stop."""
        if self._current_acquisition_id is not None:
            self.acquisition_stopped.emit(str(event.acquisition_id))
            self._current_acquisition_id = None

    def _on_sample_event(self, event: ContinuousAcquisitionSampleAcquired):
        """
        Handle sample acquired event.
        Called from executor thread - emit Qt signals for UI thread.
        """
        acquisition_id_str = str(event.acquisition_id)

        if self._current_acquisition_id is None:
            self._current_acquisition_id = acquisition_id_str
            self.acquisition_started.emit(acquisition_id_str)

        m = event.sample
        
        # 1. Construct raw measurement dict
        raw_measurement = {
            "Ux In-Phase": m.voltage_x_in_phase,
            "Ux Quadrature": m.voltage_x_quadrature,
            "Uy In-Phase": m.voltage_y_in_phase,
            "Uy Quadrature": m.voltage_y_quadrature,
            "Uz In-Phase": m.voltage_z_in_phase,
            "Uz Quadrature": m.voltage_z_quadrature,
        }
        
        # 2. Store for calibration 
        self._last_raw_sample = raw_measurement

        # 3. Process (Noise -> Phase -> Primary)
        processed_measurement = self._processor.process_sample(raw_measurement)
        
        # 4. Apply Coordinate Transformation (Sensor -> Source)
        # Transform In-Phase vector
        v_in_phase = (
            processed_measurement["Ux In-Phase"], 
            processed_measurement["Uy In-Phase"], 
            processed_measurement["Uz In-Phase"]
        )
        v_rot_in_phase = self._transformation_service.transform_sensor_to_source(v_in_phase)
        
        # Transform Quadrature vector
        v_quadrature = (
            processed_measurement["Ux Quadrature"], 
            processed_measurement["Uy Quadrature"], 
            processed_measurement["Uz Quadrature"]
        )
        v_rot_quadrature = self._transformation_service.transform_sensor_to_source(v_quadrature)

        # 5. Prepare data for UI (using transformed values)
        data = {
            "acquisition_id": acquisition_id_str,
            "index": event.sample_index,
            "measurement": {
                "Ux In-Phase": v_rot_in_phase[0],
                "Ux Quadrature": v_rot_quadrature[0],
                
                "Uy In-Phase": v_rot_in_phase[1],
                "Uy Quadrature": v_rot_quadrature[1],
                
                "Uz In-Phase": v_rot_in_phase[2],
                "Uz Quadrature": v_rot_quadrature[2],
            },
            "timestamp": event.sample.timestamp.isoformat(),
        }
        
        self.sample_acquired.emit(data)
        
        # Periodically enable UI update of angles? 
        # Or just do it when enabling. The loop is fast, we don't want to emit angles every sample.


    def shutdown(self):
        """Cleanup resources."""
        # Unsubscribe from events
        if self._event_bus:
            self._event_bus.unsubscribe("ContinuousAcquisitionSampleAcquired", self._on_sample_event)
            self._event_bus.unsubscribe("ContinuousAcquisitionFailed", self._on_failed_event)
            self._event_bus.unsubscribe("ContinuousAcquisitionStopped", self._on_stopped_event)
