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
    ContinuousAcquisitionStopped,
)
from domain.events.i_domain_event_bus import IDomainEventBus


from interface_v2.presenters.signal_processor import SignalPostProcessor

class ContinuousAcquisitionPresenter(QObject):
    """
    Presenter for Continuous Acquisition Panel.
    - Translates UI interactions to service calls
    - Subscribes to domain events and emits Qt signals
    - Handles post-processing (Noise, Phase, Primary) via SignalPostProcessor
    """

    # Signals emitted to the UI
    acquisition_started = Signal(str)  # acquisition_id
    acquisition_stopped = Signal(str)  # acquisition_id
    acquisition_failed = Signal(str)  # reason
    sample_acquired = Signal(dict)  # {acquisition_id, index, measurement:{...}, timestamp}

    def __init__(self, service: ContinuousAcquisitionService, event_bus: IDomainEventBus):
        super().__init__()
        self._service = service
        self._event_bus = event_bus
        self._current_acquisition_id: str | None = None
        
        # Signal Processor
        self._processor = SignalPostProcessor()
        self._last_raw_sample: Dict[str, float] = {}

        # Subscribe to domain events - USE EXACT CLASS NAMES (case-sensitive)
        self._event_bus.subscribe("ContinuousAcquisitionSampleAcquired", self._on_sample_event)
        self._event_bus.subscribe("ContinuousAcquisitionFailed", self._on_failed_event)
        self._event_bus.subscribe("ContinuousAcquisitionStopped", self._on_stopped_event)

    # ------------------------------------------------------------------ #
    # Calibration Commands (Logic)
    # ------------------------------------------------------------------ #
    
    @Slot()
    def calibrate_noise(self):
        """Use last received sample to calibrate noise offset."""
        if self._last_raw_sample:
            self._processor.calibrate_noise(self._last_raw_sample)
            
    @Slot()
    def calibrate_phase(self):
        """
        Use last received sample (after noise correction) to align phase.
        We must re-apply noise correction to the raw sample first to get the 'pre-phase' state.
        """
        if self._last_raw_sample:
            # 1. Apply Noise Correction only
            state_backup = self._processor.state.phase_correction_enabled
            self._processor.state.phase_correction_enabled = False # Disable temporarily
            
            pre_phase_sample = self._processor.process_sample(self._last_raw_sample)
            
            self._processor.calibrate_phase(pre_phase_sample)
            self._processor.state.phase_correction_enabled = True # Re-enable (or ensure it's on)

    @Slot()
    def calibrate_primary(self):
        """Use last received (fully processed) sample to tare primary field."""
        if self._last_raw_sample:
            # Get current processed value
            processed = self._processor.process_sample(self._last_raw_sample)
            self._processor.calibrate_primary(processed)

    @Slot()
    def reset_calibration(self):
        """Clear all offsets and corrections."""
        self._processor.reset_calibration()

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

    # ------------------------------------------------------------------ #
    # Domain Event Handlers
    # ------------------------------------------------------------------ #

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

        # 4. Prepare data for UI (using processed values)
        data = {
            "acquisition_id": acquisition_id_str,
            "index": event.sample_index,
            "measurement": {
                "Ux In-Phase": processed_measurement["Ux In-Phase"],
                "Ux Quadrature": processed_measurement["Ux Quadrature"],
                
                "Uy In-Phase": processed_measurement["Uy In-Phase"],
                "Uy Quadrature": processed_measurement["Uy Quadrature"],
                
                "Uz In-Phase": processed_measurement["Uz In-Phase"],
                "Uz Quadrature": processed_measurement["Uz Quadrature"],
            },
            "timestamp": event.sample.timestamp.isoformat(),
        }
        self.sample_acquired.emit(data)

    def shutdown(self):
        """Cleanup resources."""
        # Unsubscribe from events
        if self._event_bus:
            self._event_bus.unsubscribe("ContinuousAcquisitionSampleAcquired", self._on_sample_event)
            self._event_bus.unsubscribe("ContinuousAcquisitionFailed", self._on_failed_event)
            self._event_bus.unsubscribe("ContinuousAcquisitionStopped", self._on_stopped_event)
