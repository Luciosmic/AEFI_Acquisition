"""
Synchronous Detection Presenter - Interface V2

Bridges between SynchronousDetectionService and ExcitationPanel /
HardwareAdvancedConfigPanel. Separate presenter (not folded into
ExcitationPresenter) because it adapts a distinct service 1:1, following
the same pattern used everywhere else in this codebase.
"""

import logging

from PySide6.QtCore import QObject, Signal, Slot

from application.services.synchronous_detection_service.i_api_synchronous_detection_service import (
    IApiSynchronousDetectionService,
)
from application.services.synchronous_detection_service.synchronous_detection_service import (
    SYNCHRONOUS_DETECTION_PHASE_CALIBRATION_ENTRY_ADDED_TOPIC,
    SYNCHRONOUS_DETECTION_COMPENSATION_ENABLED_CHANGED_TOPIC,
)
from application.services.excitation_configuration_service.excitation_configuration_service import (
    EXCITATION_FREQUENCY_CHANGED_TOPIC,
    DDS_CHANNEL_CONFIG_CHANGED_TOPIC,
)

# Duplicated literal (matches this codebase's existing convention of
# re-declaring topic constants per consumer, e.g. EXCITATION_FREQUENCY_CHANGED_TOPIC
# above) rather than importing from infrastructure/ — interface must not
# depend on infrastructure. Source of truth: ad9106_advanced_configurator.py.
DDS_SYNCHRONOUS_DETECTION_CHANNEL_CHANGED_TOPIC = "ddssynchronousdetectionchannelchanged"
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus


logger = logging.getLogger(__name__)


class SynchronousDetectionPresenter(QObject):
    """
    Presenter for the "Détection synchrone" read-only display (Excitation
    panel) and the calibration/compensation controls (Hardware Advanced
    Config panel).
    - Receives UI events and calls Service
    - Emits signals for UI updates
    """

    # s1_deg, s2_deg, s3_deg, s4_deg, delta_phi_corrige_deg (float or None), lock_in_gain_below_default
    sphere_phases_updated = Signal(float, float, float, float, object, bool)
    compensation_state_changed = Signal(bool)
    status_message = Signal(str)

    def __init__(self, service: IApiSynchronousDetectionService, event_bus: IDomainEventBus):
        super().__init__()
        self._service = service
        # Any hardware state change that can move S1-S4 or Delta_Phi_corrigé
        # (frequency, DDS channel config, or a new calibration entry) should
        # refresh this panel's display instead of going stale. Construction
        # order matters: SynchronousDetectionService must already be
        # subscribed (see main.py) before this presenter, so it has
        # recomputed its own state by the time these handlers run.
        event_bus.subscribe(EXCITATION_FREQUENCY_CHANGED_TOPIC, self._on_hardware_state_changed)
        event_bus.subscribe(DDS_CHANNEL_CONFIG_CHANGED_TOPIC, self._on_hardware_state_changed)
        event_bus.subscribe(
            DDS_SYNCHRONOUS_DETECTION_CHANNEL_CHANGED_TOPIC, self._on_hardware_state_changed
        )
        event_bus.subscribe(
            SYNCHRONOUS_DETECTION_PHASE_CALIBRATION_ENTRY_ADDED_TOPIC, self._on_hardware_state_changed
        )
        event_bus.subscribe(
            SYNCHRONOUS_DETECTION_COMPENSATION_ENABLED_CHANGED_TOPIC, self._on_compensation_changed
        )

    def _on_hardware_state_changed(self, event) -> None:
        self.refresh_state()

    def _on_compensation_changed(self, event) -> None:
        self.compensation_state_changed.emit(event.enabled)

    def refresh_state(self) -> None:
        """Push the service's current sphere phases + compensation state to the UI."""
        dto = self._service.get_sphere_phases()
        self.sphere_phases_updated.emit(
            dto.s1_degrees,
            dto.s2_degrees,
            dto.s3_degrees,
            dto.s4_degrees,
            dto.delta_phi_corrige_degrees,
            dto.lock_in_gain_below_default,
        )
        self.compensation_state_changed.emit(self._service.is_compensation_enabled())

    @Slot()
    def on_save_calibration_point_requested(self) -> None:
        try:
            self._service.save_calibration_point()
            message = "Point de calibration enregistré"
            logger.info(message)
            self.status_message.emit(message)
        except Exception as e:
            message = f"Erreur: {e}"
            logger.error(message)
            self.status_message.emit(message)

    @Slot(bool)
    def on_compensation_toggle_requested(self, enabled: bool) -> None:
        logger.info("Compensation %s", "activée" if enabled else "désactivée")
        self._service.set_compensation_enabled(enabled)

    @Slot(bool)
    def on_lock_in_detection_toggled(self, enabled: bool) -> None:
        """Checked -> force ch3/ch4 gain to the recommended default.
        Unchecked -> zero ch3/ch4 gain (disables synchronous detection)."""
        logger.info("Lock-In Detection %s", "activé" if enabled else "désactivé")
        if enabled:
            self._service.enable_lock_in_detection()
        else:
            self._service.disable_lock_in_detection()

    @Slot(float)
    def on_lock_in_phase_offset_changed(self, offset_degrees: float) -> None:
        """User-edited "Lock-in Detection Phase Offset" field (Excitation
        panel) — an explicit manual value, distinct from the calibrated
        compensation correction."""
        logger.info("Lock-in Detection Phase Offset manually set to %.1f°", offset_degrees)
        self._service.set_manual_phase_offset(offset_degrees)

    @Slot()
    def on_lock_in_phase_offset_reset_requested(self) -> None:
        try:
            self._service.reset_phase_offset_to_calibrated()
            message = "Offset réinitialisé au point de calibration enregistré"
            logger.info(message)
            self.status_message.emit(message)
        except Exception as e:
            message = f"Erreur: {e}"
            logger.error(message)
            self.status_message.emit(message)
