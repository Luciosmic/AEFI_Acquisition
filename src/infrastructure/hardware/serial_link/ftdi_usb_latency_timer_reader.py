"""
FTDI USB Latency Timer Reader

See ftdi_usb_latency_timer_reader_intention.md.
"""

import logging
import sys
from typing import Callable, Iterable, Optional, Tuple

from application.services.acquisition_throughput_characterization_service.ports.i_usb_latency_timer_port import (
    IUsbLatencyTimerPort,
)
from domain.shared_kernel.operation_result import OperationResult

logger = logging.getLogger(__name__)

FTDIBUS_KEY = r"SYSTEM\CurrentControlSet\Enum\FTDIBUS"
DEVICE_PARAMETERS_SUBKEY = r"0000\Device Parameters"

# (device key, PortName, LatencyTimer) for each FTDI device in the registry.
FtdiDevice = Tuple[str, Optional[str], Optional[int]]


def enumerate_ftdi_devices_from_registry() -> Iterable[FtdiDevice]:
    """Windows only. Raises OSError if the FTDIBUS key cannot be read."""
    import winreg

    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, FTDIBUS_KEY) as root:
        index = 0
        while True:
            try:
                device = winreg.EnumKey(root, index)
            except OSError:
                return
            index += 1
            try:
                with winreg.OpenKey(root, f"{device}\\{DEVICE_PARAMETERS_SUBKEY}") as parameters:
                    port_name = _query(winreg, parameters, "PortName")
                    latency = _query(winreg, parameters, "LatencyTimer")
            except OSError:
                yield device, None, None
                continue
            yield device, port_name, latency


def _query(winreg, key, name):
    try:
        return winreg.QueryValueEx(key, name)[0]
    except OSError:
        return None


class FtdiUsbLatencyTimerReader(IUsbLatencyTimerPort):
    """Latency timer configured in the FTDI driver for the device whose
    PortName is the given serial port."""

    def __init__(
        self,
        enumerate_devices: Callable[[], Iterable[FtdiDevice]] = enumerate_ftdi_devices_from_registry,
        platform: str = sys.platform,
    ) -> None:
        self._enumerate_devices = enumerate_devices
        self._platform = platform

    def read_latency_timer_ms(self, serial_port: str) -> OperationResult[float, str]:
        if self._platform != "win32":
            return self._unknown(serial_port, f"lecture du registre FTDI possible sous Windows seulement ({self._platform})")
        try:
            devices = list(self._enumerate_devices())
        except Exception as error:  # winreg: OSError / PermissionError / ImportError — never fail the sweep
            return self._unknown(serial_port, f"registre FTDI illisible ({type(error).__name__}: {error})")
        matching = [(device, latency) for device, port, latency in devices if port == serial_port]
        if not matching:
            return self._unknown(serial_port, f"aucun périphérique FTDI déclaré sur {serial_port} dans le registre")
        if len(matching) > 1:
            logger.info(
                "FtdiUsbLatencyTimerReader: %d FTDI devices declare %s, using %s",
                len(matching), serial_port, matching[0][0],
            )
        device, latency = matching[0]
        if latency is None:
            return self._unknown(serial_port, f"LatencyTimer absent pour {device}")
        logger.info("FtdiUsbLatencyTimerReader: %s (%s) latency_timer=%s ms", serial_port, device, latency)
        return OperationResult.ok(float(latency))

    @staticmethod
    def _unknown(serial_port: str, reason: str) -> OperationResult[float, str]:
        logger.warning("FtdiUsbLatencyTimerReader: latency timer of %s unknown: %s", serial_port, reason)
        return OperationResult.fail(reason)
