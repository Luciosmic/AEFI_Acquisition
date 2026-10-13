"""
Inertial Sensor Application Service

Responsibility:
- Connect/disconnect the inertial sensor board on demand, absorbing hardware
  exceptions (reported as InertialSensorConnectionChanged).
- Thin use case that delegates continuous acquisition (start/stop) to the
  IInertialSensorAcquisitionExecutor port.
- Safety stop at application exit (shutdown): the board keeps its stream
  active with the port closed, so the stream stop must be sent.

Rationale:
- The acquisition loop (blocking reads, failure tolerance, event publication)
  is execution mechanics: it belongs in infrastructure behind the executor
  port. Same pattern as ElectricFieldProbeService.

Design:
- Connection and start are operator actions: no automatic reconnection or
  restart (visible state, user-triggered actions).
- ponytail: the lidar (a distance, not an inertial quantity) is one channel of
  the same stream because it sits on the same board and serial link — an
  infrastructure fact. Ceiling: one service and one stream carry both.
  Upgrade: a separate lidar concept and port; the shared board stays an
  infrastructure detail.
"""

from __future__ import annotations

import logging
from typing import Sequence

from application.services.inertial_sensor_service.dtos.inertial_sensor_dtos import (
    ALL_CHANNELS,
    InertialSensorAcquisitionConfig,
)
from application.services.inertial_sensor_service.i_api_inertial_sensor_service import (
    IApiInertialSensorService,
)
from application.services.inertial_sensor_service.ports.i_inertial_sensor_acquisition_executor import (
    IInertialSensorAcquisitionExecutor,
)
from application.services.inertial_sensor_service.ports.i_inertial_sensor_stream_port import (
    IInertialSensorStreamPort,
)
from domain.inertial_sensor.events.inertial_sensor_connection_changed.inertial_sensor_connection_changed import (
    InertialSensorConnectionChanged,
)
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus

CONNECTION_CHANGED_TOPIC = "inertialsensorconnectionchanged"

logger = logging.getLogger(__name__)


class InertialSensorService(IApiInertialSensorService):
    """Application service for the streamed inertial sensor."""

    def __init__(
        self,
        executor: IInertialSensorAcquisitionExecutor,
        stream_port: IInertialSensorStreamPort,
        event_bus: IDomainEventBus,
        channels: Sequence[str] = ALL_CHANNELS,
    ) -> None:
        self._executor = executor
        self._stream_port = stream_port
        self._event_bus = event_bus
        self._channels = tuple(channels)

    def connect_sensor(self) -> None:
        logger.info("InertialSensorService: Command connect_sensor")
        if self._stream_port.is_connected():
            logger.info("InertialSensorService: already connected. Doing nothing.")
            return
        try:
            self._stream_port.connect()
        except Exception as e:
            logger.error("InertialSensorService: connect_sensor failed error=%s", e)
            self._event_bus.publish(
                CONNECTION_CHANGED_TOPIC,
                InertialSensorConnectionChanged(connected=False, error=str(e)),
            )
            return
        self._event_bus.publish(
            CONNECTION_CHANGED_TOPIC, InertialSensorConnectionChanged(connected=True)
        )

    def disconnect_sensor(self) -> None:
        logger.info("InertialSensorService: Command disconnect_sensor")
        self._executor.stop()
        try:
            self._stream_port.disconnect()
        except Exception as e:
            logger.error("InertialSensorService: disconnect_sensor failed error=%s", e)
            self._event_bus.publish(
                CONNECTION_CHANGED_TOPIC,
                InertialSensorConnectionChanged(connected=False, error=str(e)),
            )
            return
        self._event_bus.publish(
            CONNECTION_CHANGED_TOPIC, InertialSensorConnectionChanged(connected=False)
        )

    def start_acquisition(self) -> None:
        logger.info("InertialSensorService: Command start_acquisition channels=%s", self._channels)
        if not self._stream_port.is_connected():
            logger.warning("InertialSensorService: start_acquisition refused, not connected.")
            return
        if self._executor.is_running():
            logger.info("InertialSensorService: acquisition already running. Doing nothing.")
            return
        self._executor.start(
            InertialSensorAcquisitionConfig(channels=self._channels), self._stream_port
        )

    def stop_acquisition(self) -> None:
        logger.info("InertialSensorService: Command stop_acquisition")
        self._executor.stop()

    def is_acquisition_running(self) -> bool:
        return self._executor.is_running()

    def shutdown(self) -> None:
        logger.info("InertialSensorService: Command shutdown (safety stop at application exit)")
        try:
            self._executor.stop()
        except Exception as e:
            logger.error("InertialSensorService: shutdown could not stop acquisition error=%s", e)
        try:
            # disconnect() sends the stream stop to the board (it keeps streaming port closed).
            self._stream_port.disconnect()
        except Exception as e:
            logger.error("InertialSensorService: shutdown could not disconnect error=%s", e)
