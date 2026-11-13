"""
Inertial Probe Application Service

Responsibility:
- Connect/disconnect the inertial probe board on demand, absorbing hardware
  exceptions (reported as InertialProbeConnectionChanged).
- Thin use case that delegates continuous acquisition (start/stop) to the
  IInertialProbeAcquisitionExecutor port.
- Safety stop at application exit (shutdown): the board keeps its stream
  active with the port closed, so the stream stop must be sent.

Rationale:
- The acquisition loop (blocking reads, failure tolerance, event publication)
  is execution mechanics: it belongs in infrastructure behind the executor
  port. Same pattern as ElectricFieldProbeService.

Design:
- Connection and start are requested from outside (panel buttons, or once at
  application startup through the same path): no automatic reconnection or
  restart.
- The lidar is one channel of the same stream (see the ponytail note below).
"""

from __future__ import annotations

import logging
from typing import Sequence

from application.inertial_probe.inertial_probe_service.dtos.inertial_probe_dtos import (
    ALL_CHANNELS,
    InertialProbeAcquisitionConfig,
)
from application.inertial_probe.inertial_probe_service.i_api_inertial_probe_service import (
    IApiInertialProbeService,
)
from application.inertial_probe.inertial_probe_service.ports.i_inertial_probe_acquisition_executor import (
    IInertialProbeAcquisitionExecutor,
)
from application.inertial_probe.inertial_probe_service.ports.i_inertial_probe_stream_port import (
    IInertialProbeStreamPort,
)
from domain.inertial_probe.events.inertial_probe_connection_changed.inertial_probe_connection_changed import (
    InertialProbeConnectionChanged,
)
from domain.shared_kernel.events.i_domain_event_bus.i_domain_event_bus import IDomainEventBus

CONNECTION_CHANGED_TOPIC = "inertialprobeconnectionchanged"

logger = logging.getLogger(__name__)


# ponytail: the lidar (a distance, not an inertial quantity) is one channel of the
# same stream because it sits on the same board and serial link — an
# infrastructure fact. Ceiling: one service and one stream carry both. Upgrade: a
# separate lidar concept and port; the shared board stays an infrastructure detail.
class InertialProbeService(IApiInertialProbeService):
    """Application service for the streamed inertial probe."""

    def __init__(
        self,
        executor: IInertialProbeAcquisitionExecutor,
        stream_port: IInertialProbeStreamPort,
        event_bus: IDomainEventBus,
        channels: Sequence[str] = ALL_CHANNELS,
    ) -> None:
        self._executor = executor
        self._stream_port = stream_port
        self._event_bus = event_bus
        self._channels = tuple(channels)

    def connect_sensor(self) -> None:
        logger.info("InertialProbeService: Command connect_sensor")
        if self._stream_port.is_connected():
            logger.info("InertialProbeService: already connected. Doing nothing.")
            return
        try:
            self._stream_port.connect()
        except Exception as e:
            logger.error("InertialProbeService: connect_sensor failed error=%s", e)
            self._event_bus.publish(
                CONNECTION_CHANGED_TOPIC,
                InertialProbeConnectionChanged(connected=False, error=str(e)),
            )
            return
        self._event_bus.publish(
            CONNECTION_CHANGED_TOPIC, InertialProbeConnectionChanged(connected=True)
        )

    def disconnect_sensor(self) -> None:
        logger.info("InertialProbeService: Command disconnect_sensor")
        self._executor.stop()
        try:
            self._stream_port.disconnect()
        except Exception as e:
            logger.error("InertialProbeService: disconnect_sensor failed error=%s", e)
            self._event_bus.publish(
                CONNECTION_CHANGED_TOPIC,
                InertialProbeConnectionChanged(connected=False, error=str(e)),
            )
            return
        self._event_bus.publish(
            CONNECTION_CHANGED_TOPIC, InertialProbeConnectionChanged(connected=False)
        )

    def start_acquisition(self) -> None:
        logger.info("InertialProbeService: Command start_acquisition channels=%s", self._channels)
        if not self._stream_port.is_connected():
            logger.warning("InertialProbeService: start_acquisition refused, not connected.")
            return
        if self._executor.is_running():
            logger.info("InertialProbeService: acquisition already running. Doing nothing.")
            return
        self._executor.start(
            InertialProbeAcquisitionConfig(channels=self._channels), self._stream_port
        )

    def stop_acquisition(self) -> None:
        logger.info("InertialProbeService: Command stop_acquisition")
        self._executor.stop()

    def is_acquisition_running(self) -> bool:
        return self._executor.is_running()

    def shutdown(self) -> None:
        logger.info("InertialProbeService: Command shutdown (safety stop at application exit)")
        try:
            self._executor.stop()
        except Exception as e:
            logger.error("InertialProbeService: shutdown could not stop acquisition error=%s", e)
        try:
            # disconnect() sends the stream stop to the board (it keeps streaming port closed).
            self._stream_port.disconnect()
        except Exception as e:
            logger.error("InertialProbeService: shutdown could not disconnect error=%s", e)
