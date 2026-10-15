"""
InertialSensorAcquisitionExecutor

Responsibility:
- Run the continuous acquisition of the inertial sensor stream in a daemon
  worker thread (start_stream blocks ~0.5 s and read_sample blocks until the
  next line: never in the Qt thread), publishing a domain event per sample.
- Always send the stream stop to the board when the worker ends: the board
  keeps its stream active until told to stop.
- Tolerate a bounded run of read errors / a bounded silence before treating
  the stream as failed.

Design:
- Non-blocking `start(config, stream_port)`; `stop()` uses an Event flag and a
  join with timeout. An operator stop publishes no failure event.
- The lidar travels as one channel of the same stream (see the ponytail note
  below).
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Optional
from uuid import UUID, uuid4

from application.services.inertial_sensor_service.dtos.inertial_sensor_dtos import (
    InertialSensorAcquisitionConfig,
)
from application.services.inertial_sensor_service.ports.i_inertial_sensor_acquisition_executor import (
    IInertialSensorAcquisitionExecutor,
)
from application.services.inertial_sensor_service.ports.i_inertial_sensor_stream_port import (
    IInertialSensorStreamPort,
)
from domain.inertial_sensor.events.inertial_sensor_sample_acquired.inertial_sensor_sample_acquired import (
    InertialSensorSampleAcquired,
)
from domain.inertial_sensor.events.inertial_sensor_stream_failed.inertial_sensor_stream_failed import (
    InertialSensorStreamFailed,
)
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus

logger = logging.getLogger(__name__)

SAMPLE_ACQUIRED_TOPIC = "inertialsensorsampleacquired"
STREAM_FAILED_TOPIC = "inertialsensorstreamfailed"


# ponytail: the lidar (a distance) travels as one channel of the same stream (see
# IInertialSensorStreamPort). Ceiling: one worker, one stream, one event carry
# both. Upgrade: a separate lidar port and executor.
class InertialSensorAcquisitionExecutor(IInertialSensorAcquisitionExecutor):
    MAX_CONSECUTIVE_READ_ERRORS = 2
    # Silence longer than this (no sample, no exception) is a stalled board.
    # At the observed 25 Hz a healthy stream never stays silent this long.
    MAX_SILENCE_S = 3.0
    # Bounds the delay between two checks of the stop flag, hence stop() latency.
    READ_TIMEOUT_S = 0.25

    def __init__(self, event_bus: IDomainEventBus) -> None:
        self._event_bus = event_bus
        self._thread: Optional[threading.Thread] = None
        self._stop_flag = threading.Event()

    def start(
        self,
        config: InertialSensorAcquisitionConfig,
        stream_port: IInertialSensorStreamPort,
    ) -> None:
        if self._thread and self._thread.is_alive():
            logger.info("InertialSensorAcquisitionExecutor: already running. Doing nothing.")
            return
        self._stop_flag.clear()
        acquisition_id = uuid4()
        logger.info(
            "InertialSensorAcquisitionExecutor: start acquisition_id=%s channels=%s",
            acquisition_id,
            config.channels,
        )
        self._thread = threading.Thread(
            target=self._worker,
            args=(acquisition_id, config, stream_port),
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_flag.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    # ------------------------------------------------------------------ #
    # Internal worker
    # ------------------------------------------------------------------ #

    def _worker(
        self,
        acquisition_id: UUID,
        config: InertialSensorAcquisitionConfig,
        stream_port: IInertialSensorStreamPort,
    ) -> None:
        index = 0
        consecutive_errors = 0
        last_progress = time.monotonic()
        try:
            stream_port.start_stream(config.channels)  # blocks ~0.5 s on the real board
            while not self._stop_flag.is_set():
                try:
                    sample = stream_port.read_sample(self.READ_TIMEOUT_S)
                except Exception as e:
                    consecutive_errors += 1
                    logger.warning(
                        "InertialSensorAcquisitionExecutor: read failed acquisition_id=%s (%d/%d) error=%s",
                        acquisition_id,
                        consecutive_errors,
                        self.MAX_CONSECUTIVE_READ_ERRORS,
                        e,
                    )
                    if consecutive_errors > self.MAX_CONSECUTIVE_READ_ERRORS:
                        self._publish_failure(acquisition_id, str(e))
                        return
                    continue
                consecutive_errors = 0
                if sample is None:
                    if time.monotonic() - last_progress > self.MAX_SILENCE_S:
                        self._publish_failure(
                            acquisition_id, f"no sample for {self.MAX_SILENCE_S:.1f} s"
                        )
                        return
                    continue
                last_progress = time.monotonic()
                self._event_bus.publish(
                    SAMPLE_ACQUIRED_TOPIC,
                    InertialSensorSampleAcquired(
                        acquisition_id=acquisition_id,
                        sample_index=index,
                        timestamp_s=sample.timestamp_s,
                        acceleration_g=sample.acceleration_g,
                        angular_rate_dps=sample.angular_rate_dps,
                        magnetic_field_ut=sample.magnetic_field_ut,
                        lidar_distance_mm=sample.lidar_distance_mm,
                    ),
                )
                index += 1
        except Exception as e:
            logger.error(
                "InertialSensorAcquisitionExecutor: stream failed acquisition_id=%s error=%s",
                acquisition_id,
                e,
            )
            self._publish_failure(acquisition_id, str(e))
        finally:
            try:
                stream_port.stop_stream()  # the board keeps streaming until told to stop
            except Exception as e:
                logger.error(
                    "InertialSensorAcquisitionExecutor: stop_stream failed acquisition_id=%s error=%s",
                    acquisition_id,
                    e,
                )
            logger.info(
                "InertialSensorAcquisitionExecutor: ended acquisition_id=%s samples=%d",
                acquisition_id,
                index,
            )

    def _publish_failure(self, acquisition_id: UUID, reason: str) -> None:
        self._event_bus.publish(
            STREAM_FAILED_TOPIC,
            InertialSensorStreamFailed(acquisition_id=acquisition_id, reason=reason),
        )
