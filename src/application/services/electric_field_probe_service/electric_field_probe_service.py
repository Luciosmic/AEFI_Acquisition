"""
Electric Field Probe Application Service

Responsibility:
- Connect/disconnect the probe on demand, absorbing hardware exceptions.
- Thin use case that delegates continuous acquisition (start/stop/update) to
  the IElectricFieldProbeAcquisitionExecutor port.

Rationale:
- The acquisition loop (rate control, retry policy, event publication) is
  execution mechanics, not use-case orchestration — it belongs in
  infrastructure behind the executor port. Same pattern as
  AefiAcquisitionService / IAefiAcquisitionExecutor for the AEFI channel.
"""

from __future__ import annotations

from application.services.electric_field_probe_service.i_api_electric_field_probe_service import (
    IApiElectricFieldProbeService,
)
from application.services.electric_field_probe_service.ports.i_electric_field_probe_port import (
    IElectricFieldProbePort,
)
from application.services.electric_field_probe_service.ports.i_electric_field_probe_acquisition_executor import (
    IElectricFieldProbeAcquisitionExecutor,
)
from application.services.electric_field_probe_service.dtos.electric_field_probe_dtos import (
    ElectricFieldProbeAcquisitionConfig,
    FrequencyCorrectionResult,
)
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus
from domain.shared_kernel.events.excitation_frequency_changed.excitation_frequency_changed import (
    ExcitationFrequencyChanged,
)
from domain.electric_field_probe.events.electric_field_probe_connection_changed.electric_field_probe_connection_changed import (
    ElectricFieldProbeConnectionChanged,
)
from domain.electric_field_probe.events.electric_field_probe_battery_refreshed.electric_field_probe_battery_refreshed import (
    ElectricFieldProbeBatteryRefreshed,
)
from domain.electric_field_probe.events.electric_field_probe_frequency_correction_changed.electric_field_probe_frequency_correction_changed import (
    ElectricFieldProbeFrequencyCorrectionChanged,
)

CONNECTION_CHANGED_TOPIC = "electricfieldprobeconnectionchanged"
BATTERY_REFRESHED_TOPIC = "electricfieldprobebatteryrefreshed"
EXCITATION_FREQUENCY_CHANGED_TOPIC = "excitationfrequencychanged"
FREQUENCY_CORRECTION_CHANGED_TOPIC = "electricfieldprobefrequencycorrectionchanged"


class ElectricFieldProbeService(IApiElectricFieldProbeService):
    """Application service for a generic electric field probe."""

    def __init__(
        self,
        executor: IElectricFieldProbeAcquisitionExecutor,
        probe_port: IElectricFieldProbePort,
        event_bus: IDomainEventBus,
    ) -> None:
        self._executor = executor
        self._probe_port = probe_port
        self._event_bus = event_bus
        self._last_known_excitation_frequency_hz: float = 0.0  # mirrors ExcitationParameters.off().frequency
        self._event_bus.subscribe(
            EXCITATION_FREQUENCY_CHANGED_TOPIC, self._on_excitation_frequency_changed
        )

    def connect_probe(self) -> None:
        try:
            self._probe_port.connect()
        except Exception as e:
            self._event_bus.publish(
                CONNECTION_CHANGED_TOPIC,
                ElectricFieldProbeConnectionChanged(connected=False, error=str(e)),
            )
            return
        result = self._probe_port.apply_frequency_correction(
            self._last_known_excitation_frequency_hz
        )
        self._publish_frequency_correction(result)
        self._event_bus.publish(
            CONNECTION_CHANGED_TOPIC,
            ElectricFieldProbeConnectionChanged(
                connected=True, probe=self._probe_port.get_probe()
            ),
        )

    def disconnect_probe(self) -> None:
        self._probe_port.disconnect()
        self._event_bus.publish(
            CONNECTION_CHANGED_TOPIC,
            ElectricFieldProbeConnectionChanged(connected=False),
        )

    def start_acquisition(self, config: ElectricFieldProbeAcquisitionConfig) -> None:
        self._executor.start(config, self._probe_port)

    def stop_acquisition(self) -> None:
        self._executor.stop()

    def update_acquisition_parameters(
        self, config: ElectricFieldProbeAcquisitionConfig
    ) -> None:
        # Unlike AefiAcquisitionExecutor.update_config (applied on the next
        # start, since the worker closure never re-reads self._config), a
        # running Narda stream must be restarted for a new sample_rate_hz to
        # take effect — dt is computed once at loop entry.
        if self._executor.is_running():
            self._executor.stop()
        self._executor.start(config, self._probe_port)

    def is_acquisition_running(self) -> bool:
        return self._executor.is_running()

    def refresh_battery(self) -> None:
        # Le lien serie est partage avec l'acquisition en cours (get_battery_voltage
        # entrelacerait ses propres trames avec celles du flux) : on refuse silencieusement
        # plutot que de risquer de corrompre une acquisition en cours. Le bouton UI est deja
        # desactive pendant l'acquisition (cf. panel) — cette garde est la protection de fond.
        if not self._probe_port.is_connected() or self._executor.is_running():
            return
        self._probe_port.refresh_battery()
        self._event_bus.publish(
            BATTERY_REFRESHED_TOPIC,
            ElectricFieldProbeBatteryRefreshed(probe=self._probe_port.get_probe()),
        )

    def _on_excitation_frequency_changed(self, event: ExcitationFrequencyChanged) -> None:
        self._last_known_excitation_frequency_hz = event.frequency_hz
        if not self._probe_port.is_connected():
            return
        if self._executor.is_running():
            # Le worker applique et publie lui-meme (seul a toucher le port serie pendant
            # le streaming) — cf. request_frequency_correction.
            self._executor.request_frequency_correction(event.frequency_hz)
            return
        result = self._probe_port.apply_frequency_correction(event.frequency_hz)
        self._publish_frequency_correction(result)

    def _publish_frequency_correction(self, result: FrequencyCorrectionResult) -> None:
        self._event_bus.publish(
            FREQUENCY_CORRECTION_CHANGED_TOPIC,
            ElectricFieldProbeFrequencyCorrectionChanged(
                requested_hz=result.requested_hz,
                applied_hz=result.applied_hz,
                in_range=result.in_range,
                error=result.error,
            ),
        )
