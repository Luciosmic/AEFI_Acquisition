from abc import ABC, abstractmethod

from domain.shared_kernel.operation_result import OperationResult


class IUsbLatencyTimerPort(ABC):
    """
    Responsibility:
    - Read the USB latency timer (ms) of the USB-serial bridge behind a
      serial port (e.g. "COM10").

    Rationale:
    - On the bench, T0 (fixed cost per sample) was 23.6 ms with the FTDI
      latency timer at 16 ms and 7.6 ms at 1 ms: a throughput result is
      meaningless without it, and no part of the application knows it.

    Design:
    - Returns a failure (never raises) when it cannot be read: other OS,
      non-FTDI bridge, unknown port, registry not readable.
    """

    @abstractmethod
    def read_latency_timer_ms(self, serial_port: str) -> OperationResult[float, str]: ...
