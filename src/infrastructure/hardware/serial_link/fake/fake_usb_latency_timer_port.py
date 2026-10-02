"""
Fake USB Latency Timer Port

See fake_usb_latency_timer_port_intention.md.
"""

from typing import List, Optional

from application.shared.acquisition_parameters.i_usb_latency_timer_port import (
    IUsbLatencyTimerPort,
)
from domain.shared_kernel.operation_result import OperationResult


class FakeUsbLatencyTimerPort(IUsbLatencyTimerPort):
    """`latency_ms` for `serial_port` (default COM10); any other port, or
    `failure` set, fails like the real reader."""

    def __init__(self, latency_ms: float = 16.0, serial_port: str = "COM10", failure: Optional[str] = None) -> None:
        self._latency_ms = latency_ms
        self._serial_port = serial_port
        self._failure = failure
        self.requested_ports: List[str] = []

    def read_latency_timer_ms(self, serial_port: str) -> OperationResult[float, str]:
        self.requested_ports.append(serial_port)
        if self._failure is not None:
            return OperationResult.fail(self._failure)
        if serial_port != self._serial_port:
            return OperationResult.fail(f"aucun périphérique FTDI déclaré sur {serial_port} dans le registre")
        return OperationResult.ok(self._latency_ms)
