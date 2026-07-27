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
)
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus
from domain.electric_field_probe.events.electric_field_probe_connection_changed.electric_field_probe_connection_changed import (
    ElectricFieldProbeConnectionChanged,
)

CONNECTION_CHANGED_TOPIC = "electricfieldprobeconnectionchanged"


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

    def connect_probe(self) -> None:
        try:
            self._probe_port.connect()
        except Exception as e:
            self._event_bus.publish(
                CONNECTION_CHANGED_TOPIC,
                ElectricFieldProbeConnectionChanged(connected=False, error=str(e)),
            )
            return
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
