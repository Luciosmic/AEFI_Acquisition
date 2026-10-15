"""Serial driver for the LSM9DS1 board in continuous (stream) mode.

Blocking acquisition (no thread, no callback): the caller loops on read_sample().
start_stream() blocks ~0.5 s (commands spaced by 100 ms) — call it from a worker
thread, never from the Qt thread.
"""

import time
from collections import deque
from typing import Callable, Deque, Dict, Optional, Sequence, Tuple

import serial

from infrastructure.hardware.lsm9ds1.lsm9ds1_stream_protocol import (
    STOP_COMMAND,
    VALID_RATES_HZ,
    LineSplitter,
    normalize_sensors,
    parse_stream_line,
    start_commands,
)

RawLine = Dict[str, Tuple[int, ...]]


class LSM9DS1StreamDriver:
    def __init__(
        self,
        port: str,
        baudrate: int,
        timeout: float = 0.05,
        command_spacing_s: float = 0.1,
        serial_factory: Callable = serial.Serial,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._port = port
        self._baudrate = baudrate
        self._timeout = timeout
        self._spacing = command_spacing_s
        self._serial_factory = serial_factory
        self._sleep = sleep
        self._clock = clock
        self._ser: Optional[object] = None
        self._sensors: Optional[Tuple[str, ...]] = None
        self._splitter = LineSplitter()
        self._pending: Deque[Tuple[float, RawLine]] = deque()
        self.dropped_lines = 0

    def connect(self) -> None:
        if self._ser is not None:
            return
        self._ser = self._serial_factory(self._port, self._baudrate, timeout=self._timeout)
        self._stop_and_flush()  # a stream may have survived the previous port closing

    def disconnect(self) -> None:
        if self._ser is not None:
            self._stop_and_flush()
            self._ser.close()  # type: ignore[attr-defined]
            self._ser = None
        self._sensors = None

    def is_connected(self) -> bool:
        return self._ser is not None

    def start_stream(self, sensors: Sequence[str], rate_hz: Optional[int] = None) -> None:
        if self._ser is None:
            raise RuntimeError("LSM9DS1 not connected")
        order = normalize_sensors(sensors)
        if rate_hz is not None and rate_hz not in VALID_RATES_HZ:
            raise ValueError(f"rate_hz must be one of {VALID_RATES_HZ}")
        self._stop_and_flush()
        self._splitter = LineSplitter()
        self._pending.clear()
        self.dropped_lines = 0
        if rate_hz is not None:
            self._send(f"F{rate_hz}*")
            self._sleep(self._spacing)
        for cmd in start_commands(order):
            self._send(cmd)
            self._sleep(self._spacing)
        self._sensors = order

    def stop_stream(self) -> None:
        if self._ser is not None:
            self._stop_and_flush()
        self._sensors = None

    def read_sample(self, timeout_s: float = 1.0) -> Optional[Tuple[float, RawLine]]:
        if self._ser is None or self._sensors is None:
            raise RuntimeError("stream not started")
        deadline = self._clock() + timeout_s
        while True:
            if self._pending:
                return self._pending.popleft()
            n = getattr(self._ser, "in_waiting", 0) or 1
            chunk = self._ser.read(n)  # type: ignore[attr-defined]
            t = self._clock()
            for line in self._splitter.feed(chunk):
                parsed = parse_stream_line(line, self._sensors)
                if parsed is None:
                    self.dropped_lines += 1  # transient or truncated line
                else:
                    self._pending.append((t, parsed))
            if not self._pending and t >= deadline:
                return None

    def _send(self, command: str) -> None:
        self._ser.write(command.encode("ascii"))  # type: ignore[attr-defined]

    def _stop_and_flush(self) -> None:
        self._send(STOP_COMMAND)
        self._sleep(self._spacing)  # up to ~50 ms of lines still in flight after S*
        self._ser.reset_input_buffer()  # type: ignore[attr-defined]
