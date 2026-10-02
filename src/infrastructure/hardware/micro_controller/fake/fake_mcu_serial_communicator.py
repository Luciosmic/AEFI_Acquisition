"""
Fake MCU Serial Communicator

Responsibility:
- In-memory double of MCU_SerialCommunicator for "mock mode" app runs and tests.
- Same public contract: connect(), disconnect(), send_command() -> (bool, str).
"""

import math
import random
import time
from typing import Optional


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

    def __init__(
        self,
        n_channels: int = 6,
        acquisition_delay_s: float = 0.05,
        adc_output_rate_hz: Optional[float] = None,
        noise_std_counts: float = 2.0,
    ) -> None:
        """`acquisition_delay_s`: fixed cost T0 of one 'm<n>' round-trip.
        `adc_output_rate_hz`: if set, the MCU also waits n conversions of the
        ADC (T(n) = T0 + n/ODR), as the real MCU averaging does. ponytail:
        T0/ODR are hypotheses until the bench throughput characterization
        measures them — replace by the measured values.
        `noise_std_counts`: white noise of ONE ADC conversion (counts); the
        MCU average of n conversions has σ/√n."""
        self._connected = False
        self._n_channels = n_channels
        self._adc_output_rate_hz = adc_output_rate_hz
        self._noise_std_counts = noise_std_counts
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
            n_avg = max(1, int(command[1:].replace('*', '')))
            delay = self._acquisition_delay_s
            if self._adc_output_rate_hz:
                delay += n_avg / self._adc_output_rate_hz
            if delay > 0:
                time.sleep(delay)
            # ADC-level noise only (a few counts, µV scale): the MCU itself
            # (this class) only relays and averages. Was +/-50_000 counts
            # (~+/-14.5mV), which swamped CubeSensorFieldSimulator's mV-scale
            # excitation signal; that noise belongs at the source (DDS jitter)
            # and sensor (electronics) level — see CubeSensorFieldSimulator.
            sigma = self._noise_std_counts / math.sqrt(n_avg)
            codes = [round(random.gauss(0.0, sigma)) for _ in range(self._n_channels)]
            return True, "\t".join(str(c) for c in codes)

        return True, "OK"
