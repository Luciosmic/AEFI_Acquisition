"""
LIDAR Distance Stream Adapter

See adapter_lidar_distance_port_intention.md.
"""

import logging
import queue
import threading
from typing import Optional

from application.services.lidar_distance.dtos.lidar_distance_dtos import (
    LidarDistanceReading,
)
from application.services.lidar_distance.ports.i_lidar_distance_port import (
    ILidarDistancePort,
)
from application.services.lidar_distance.ports.lidar_stream_error import (
    LidarStreamBusyError,
    LidarUnavailableError,
)
from application.services.inertial_sensor_service.dtos.inertial_sensor_dtos import LIDAR_CHANNEL
from application.services.inertial_sensor_service.ports.i_inertial_sensor_acquisition_executor import (
    IInertialSensorAcquisitionExecutor,
)
from application.services.inertial_sensor_service.ports.i_inertial_sensor_stream_port import (
    IInertialSensorStreamPort,
)

logger = logging.getLogger(__name__)

# Same tolerance as InertialSensorAcquisitionExecutor before a stream is declared failed.
MAX_CONSECUTIVE_READ_ERRORS = 2
# Bounds the latency of close() (the reader checks its stop flag between reads).
READ_TIMEOUT_S = 0.25


class LidarDistanceStreamAdapter(ILidarDistancePort):
    """ILidarDistancePort over the inertial board stream (LIDAR channel only)."""

    def __init__(
        self,
        stream_port: IInertialSensorStreamPort,
        panel_executor: Optional[IInertialSensorAcquisitionExecutor] = None,
    ) -> None:
        """`panel_executor`: the sensor panel's acquisition executor — while it
        runs, the board stream belongs to the panel."""
        self._stream_port = stream_port
        self._panel_executor = panel_executor
        self._readings: "queue.Queue" = queue.Queue()
        self._reader: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._connected_here = False
        self._failure: Optional[str] = None

    def is_streamed_elsewhere(self) -> bool:
        return self._panel_executor is not None and self._panel_executor.is_running()

    def open(self) -> None:
        if self.is_streamed_elsewhere():
            raise LidarStreamBusyError("le panneau du capteur inertiel diffuse déjà le flux")
        if self._reader is not None and self._reader.is_alive():
            logger.info("LidarDistanceStreamAdapter: already open. Doing nothing.")
            return
        try:
            if not self._stream_port.is_connected():
                logger.info("LidarDistanceStreamAdapter: connecting the inertial board for the LIDAR stream")
                self._stream_port.connect()
                self._connected_here = True
            self._stream_port.start_stream([LIDAR_CHANNEL])  # blocks ~0.5 s on the real board
        except Exception as error:
            logger.error("LidarDistanceStreamAdapter: open failed error=%s", error)
            self._disconnect_if_connected_here()
            raise LidarUnavailableError(f"ouverture du flux LIDAR impossible : {error}") from error
        self._readings = queue.Queue()
        self._failure = None
        self._stop.clear()
        self._reader = threading.Thread(target=self._read_loop, daemon=True, name="lidar-distance-reader")
        self._reader.start()
        logger.info("LidarDistanceStreamAdapter: LIDAR stream open (connected_here=%s)", self._connected_here)

    def read_distance(self, timeout_s: float) -> Optional[LidarDistanceReading]:
        try:
            if timeout_s <= 0:
                return self._readings.get_nowait()
            return self._readings.get(timeout=timeout_s)
        except queue.Empty:
            if self._failure is not None:
                raise LidarUnavailableError(self._failure)
            return None

    def close(self) -> None:
        reader, self._reader = self._reader, None
        if reader is not None:
            self._stop.set()
            reader.join(timeout=2.0)
        try:
            if reader is not None:
                self._stream_port.stop_stream()  # the board keeps streaming until told to stop
        except Exception as error:
            logger.error("LidarDistanceStreamAdapter: stop_stream failed error=%s", error)
        finally:
            self._disconnect_if_connected_here()
        if reader is not None:
            logger.info("LidarDistanceStreamAdapter: LIDAR stream closed")

    def _read_loop(self) -> None:
        """Reads continuously so that each distance is timestamped at its arrival
        (the driver stamps a line when it is read)."""
        errors = 0
        count = 0
        no_return = 0
        while not self._stop.is_set():
            try:
                sample = self._stream_port.read_sample(READ_TIMEOUT_S)
            except Exception as error:
                errors += 1
                logger.warning("LidarDistanceStreamAdapter: read failed (%d/%d) error=%s",
                               errors, MAX_CONSECUTIVE_READ_ERRORS, error)
                if errors > MAX_CONSECUTIVE_READ_ERRORS:
                    self._failure = f"lecture du flux LIDAR en échec : {error}"
                    return
                continue
            errors = 0
            if sample is None or sample.lidar_distance is None:
                continue
            distance = sample.lidar_distance
            self._readings.put(LidarDistanceReading(sample.timestamp_s, distance))
            count += 1
            no_return += not distance.has_return
        logger.info("LidarDistanceStreamAdapter: reader stopped after %d reading(s) rejected_zero=%d (no return)",
                    count, no_return)

    def _disconnect_if_connected_here(self) -> None:
        if not self._connected_here:
            return
        try:
            self._stream_port.disconnect()
        except Exception as error:
            logger.error("LidarDistanceStreamAdapter: disconnect failed error=%s", error)
        self._connected_here = False
