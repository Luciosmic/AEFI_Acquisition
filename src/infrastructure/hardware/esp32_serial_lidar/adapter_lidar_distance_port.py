"""
ESP32 Serial LIDAR Adapter

See adapter_lidar_distance_port_intention.md.
"""

import logging
import queue
import threading
import time
from typing import Callable, Optional

import serial

from application.services.bar_transmission_calibration_service.dtos.bar_transmission_calibration_dtos import (
    LidarDistanceReading,
)
from application.services.bar_transmission_calibration_service.ports.i_lidar_distance_port import (
    ILidarDistancePort,
)
from application.services.bar_transmission_calibration_service.ports.lidar_stream_error import (
    LidarUnavailableError,
)
from domain.shared_kernel.value_objects.lidar_distance.lidar_distance import LidarDistance

logger = logging.getLogger(__name__)

# ponytail: raw value assumed in millimetres (order of magnitude plausible: ~1.23 m
# on the bench, 2026-10-30), factor and offset not measured by us. The calibration
# does not depend on it (linearity and missed steps are relative).
# Upgrade: verify against 3 known distances.
MM_PER_LSB = 1.0
# Same tolerance as the inertial-board LIDAR adapter before the stream is declared failed.
MAX_CONSECUTIVE_READ_ERRORS = 2
# Serial read timeout: bounds the latency of close() (the reader checks its stop flag between reads).
READ_TIMEOUT_S = 0.25
# A valid line is ~11 bytes ("1227 1230\r\n"); beyond this without a line end, the buffer is garbage.
MAX_LINE_BYTES = 64


def parse_raw_distance(line: bytes) -> Optional[int]:
    """Raw distance of a `"<raw> <moving average>"` line, or None if unreadable.

    The second column (the ESP32's moving average of the last 10 raw values) is
    validated but discarded: it keeps ~2 s of memory after a move."""
    fields = line.strip().split()
    if len(fields) != 2:
        return None
    try:
        raw, _average = int(fields[0]), int(fields[1])
    except ValueError:
        return None
    return raw


class Esp32SerialLidarAdapter(ILidarDistancePort):
    """ILidarDistancePort over an ESP32 that streams `"<raw> <average>\\r\\n"` lines.

    One instance per physical LIDAR (one serial port each)."""

    def __init__(
        self,
        port: str,
        baudrate: int,
        serial_factory: Callable = serial.Serial,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._port = port
        self._baudrate = baudrate
        self._serial_factory = serial_factory
        self._clock = clock
        self._ser = None
        self._readings: "queue.Queue" = queue.Queue()
        self._reader: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._failure: Optional[str] = None

    def is_streamed_elsewhere(self) -> bool:
        return False  # its own serial port: no in-process co-owner

    def open(self) -> None:
        if self._reader is not None and self._reader.is_alive():
            logger.info("Esp32SerialLidarAdapter: already open port=%s. Doing nothing.", self._port)
            return
        logger.info("Esp32SerialLidarAdapter: opening LIDAR stream port=%s baudrate=%d", self._port, self._baudrate)
        try:
            self._ser = self._serial_factory(self._port, self._baudrate, timeout=READ_TIMEOUT_S)
            self._ser.reset_input_buffer()  # only lines arriving from now on
        except Exception as error:
            logger.error("Esp32SerialLidarAdapter: open failed port=%s error=%s", self._port, error)
            self._close_serial()
            raise LidarUnavailableError(f"ouverture du LIDAR sur {self._port} impossible : {error}") from error
        self._readings = queue.Queue()
        self._failure = None
        self._stop.clear()
        self._reader = threading.Thread(target=self._read_loop, daemon=True, name=f"lidar-esp32-reader-{self._port}")
        self._reader.start()
        logger.info("Esp32SerialLidarAdapter: LIDAR stream open port=%s", self._port)

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
        self._close_serial()
        if reader is not None:
            logger.info("Esp32SerialLidarAdapter: LIDAR stream closed port=%s", self._port)

    def _read_loop(self) -> None:
        """Reads continuously so that each distance is timestamped at its arrival."""
        buffer = b""
        first_line = True  # the port opens mid-line: "27 1230" would pass for a distance
        errors = count = no_return = unreadable = 0
        while not self._stop.is_set():
            try:
                chunk = self._ser.read(self._ser.in_waiting or 1)
            except Exception as error:
                errors += 1
                logger.warning("Esp32SerialLidarAdapter: read failed port=%s (%d/%d) error=%s",
                               self._port, errors, MAX_CONSECUTIVE_READ_ERRORS, error)
                if errors > MAX_CONSECUTIVE_READ_ERRORS:
                    self._failure = f"lecture du LIDAR sur {self._port} en échec : {error}"
                    break
                continue
            errors = 0
            if not chunk:
                continue
            t = self._clock()
            *lines, buffer = (buffer + chunk).split(b"\n")
            if len(buffer) > MAX_LINE_BYTES:  # no line end: garbage, not a line in progress
                lines.append(buffer)
                buffer = b""
            for line in lines:
                if first_line:
                    first_line = False
                    continue
                raw = parse_raw_distance(line)
                if raw is None:
                    unreadable += 1
                    logger.debug("Esp32SerialLidarAdapter: unreadable line port=%s line=%r", self._port, line)
                    continue
                distance = LidarDistance.from_raw(raw, MM_PER_LSB)
                self._readings.put(LidarDistanceReading(t, distance))
                count += 1
                no_return += not distance.has_return
        logger.info("Esp32SerialLidarAdapter: reader stopped port=%s readings=%d rejected_zero=%d (no return) "
                    "unreadable_lines=%d", self._port, count, no_return, unreadable)

    def _close_serial(self) -> None:
        ser, self._ser = self._ser, None
        if ser is None:
            return
        try:
            ser.close()
        except Exception as error:
            logger.error("Esp32SerialLidarAdapter: serial close failed port=%s error=%s", self._port, error)
