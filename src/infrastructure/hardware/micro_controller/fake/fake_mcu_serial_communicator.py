"""
Fake MCU Serial Communicator

Responsibility:
- In-memory double of MCU_SerialCommunicator for "mock mode" app runs and tests.
- Same public contract: connect(), disconnect(), send_command() -> (bool, str).
"""

import random
import time


class _FakeSerialHandle:
    """Minimal stand-in for the pyserial `Serial` object MCULifecycleAdapter.
    verify_all() reaches into directly (`communicator.ser.is_open`)."""

    def __init__(self, is_open: bool) -> None:
        self.is_open = is_open


class FakeMCUSerialCommunicator:
    """
    Stands in for MCU_SerialCommunicator with no real serial port. Lets the
    REAL AD9106Controller/ADS131Controller/adapters/configurators run
    unmodified — only this transport layer is faked.
    """

    def __init__(self, n_channels: int = 6, acquisition_delay_s: float = 0.05) -> None:
        self._connected = False
        self._n_channels = n_channels
        # AdapterAefiAcquisitionAds131a04's continuous loop has NO software
        # pacing of its own — it deliberately relies on the real ADC round-trip
        # (OSR x n_avg) to throttle itself. Without this delay, the fake
        # returns near-instantly and the loop floods the event bus / Qt main
        # thread with hundreds of thousands of samples/s, freezing or
        # crashing the app shortly after starting continuous acquisition.
        # 10ms (100Hz) — 1kHz still saturated the UI in practice.
        self._acquisition_delay_s = acquisition_delay_s
        self.ser = None  # mirrors MCU_SerialCommunicator.ser, read by MCULifecycleAdapter.verify_all()

    def connect(self, port=None, baudrate=9600) -> bool:
        self._connected = True
        self.ser = _FakeSerialHandle(is_open=True)
        return True

    def disconnect(self) -> None:
        self._connected = False
        if self.ser:
            self.ser.is_open = False

    def send_command(self, command: str):
        if not self._connected:
            return False, "Not connected"

        if not command.endswith('*'):
            command += '*'

        # Mirrors MCU_SerialCommunicator's own dispatch: 'm<n>' is the ADS131
        # acquisition command — every other command (AD9106 'a'/'d' register
        # writes, ADS131/MCU config commands) only needs a bare ack.
        if command.startswith('m') and command[1:].replace('*', '').isdigit():
            if self._acquisition_delay_s > 0:
                time.sleep(self._acquisition_delay_s)
            # +/-2 counts: genuine ADS131A04 (ADC) quantization dither, not
            # an injected noise floor — the MCU itself (this class) only
            # relays serial commands and introduces no noise of its own.
            # Was +/-50_000 (~+/-14.5mV), which swamped
            # CubeSensorFieldSimulator's mV-scale excitation signal; that
            # noise belongs at the source (DDS jitter) and sensor
            # (electronics) level instead — see CubeSensorFieldSimulator.
            codes = [random.randint(-2, 2) for _ in range(self._n_channels)]
            return True, "\t".join(str(c) for c in codes)

        return True, "OK"
