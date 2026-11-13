"""ColumnStabilization on a fake clock: the accelerometer stream is simulated by
publishing samples on a real in-memory bus as the fake time advances."""

import math
from types import SimpleNamespace

import pytest

from application.scan.scan_application_service.column_stabilization.column_stabilization import (
    ACCELEROMETER,
    FIXED_DELAY,
    INERTIAL_PROBE_SAMPLE_TOPIC,
    INTERRUPTED,
    TIMEOUT,
    ColumnStabilization,
)
from infrastructure.in_memory_event_bus.in_memory_event_bus import InMemoryEventBus

RATE_HZ = 25.0
REST_G = 0.002  # amplitude of the still column


class FakeBench:
    """Fake time + accelerometer: `sleep` advances time and streams the samples in between.

    `amplitude(t)` gives the vibration amplitude (g) at time t; `silent(t)` mutes the stream.
    """

    def __init__(self, bus, amplitude=lambda t: REST_G, silent=lambda t: False):
        self.bus, self.amplitude, self.silent = bus, amplitude, silent
        self.now = 0.0
        self.k = 0  # index of the next sample

    def clock(self):
        return self.now

    def sleep(self, dt):
        end = self.now + dt
        while (self.k / RATE_HZ) <= end:
            t = self.k / RATE_HZ
            if not self.silent(t):
                a = self.amplitude(t) * (1 if self.k % 2 else -1)
                self.bus.publish(INERTIAL_PROBE_SAMPLE_TOPIC, SimpleNamespace(
                    timestamp_s=t, acceleration_g=(a, 0.0, 1.0)))
            self.k += 1
        self.now = end


def _setup(amplitude=lambda t: REST_G, silent=lambda t: False, warm_up_s=2.0):
    bus = InMemoryEventBus()
    bench = FakeBench(bus, amplitude, silent)
    stabilization = ColumnStabilization(bus, clock=bench.clock, sleep=bench.sleep)
    bench.sleep(warm_up_s)  # the operator started the accelerometer before the scan
    return stabilization, bench


def _never():
    return False


def test_rest_level_measured_over_ten_seconds_before_the_first_move() -> None:
    stabilization, bench = _setup()
    start = bench.now
    measurement = stabilization.measure_rest("scan-1", _never)
    rest = measurement.vibration_g
    assert rest == pytest.approx(REST_G, rel=1e-3)
    assert measurement.sample_count == 251 and measurement.unavailable_reason is None  # 10 s at 25 Hz, both ends
    assert bench.now - start == pytest.approx(10.0)


def test_no_rest_level_when_the_accelerometer_is_not_streaming():
    stabilization, bench = _setup(silent=lambda t: True)
    start = bench.now
    measurement = stabilization.measure_rest("scan-1", _never)
    assert measurement.vibration_g is None
    assert measurement.unavailable_reason == "accéléromètre non en acquisition au démarrage du scan"
    assert bench.now == start  # no 10 s wait for nothing


def test_no_rest_level_when_the_accelerometer_falls_silent_during_the_measurement():
    stabilization, _ = _setup(silent=lambda t: t > 2.1)
    assert stabilization.measure_rest("scan-1", _never).vibration_g is None


def test_waits_until_the_column_is_back_at_rest_after_the_move():
    stop = 12.0
    # 20× the rest amplitude right after the stop, decaying with τ = 1 s: back under 1.5× at ~3 s.
    stabilization, bench = _setup(amplitude=lambda t: REST_G * (1 + 19 * math.exp(-(t - stop))) if t >= stop
                                  else REST_G)
    rest = stabilization.measure_rest("scan-1", _never).vibration_g
    bench.sleep(stop - bench.now)
    outcome = stabilization.wait_until_settled("scan-1", "point 0", rest, bench.now, 0.3, _never)
    assert outcome.method == ACCELEROMETER
    assert 2.0 < outcome.waited_s < 5.0
    assert outcome.vibration_g <= outcome.threshold_g == pytest.approx(1.5 * rest)


def test_never_shorter_than_the_fixed_delay_nor_than_one_window() -> None:
    stabilization, bench = _setup()
    rest = stabilization.measure_rest("scan-1", _never).vibration_g
    stop = bench.now
    assert stabilization.wait_until_settled("s", "p", rest, stop, 0.3, _never).waited_s == pytest.approx(1.0)
    stop = bench.now
    assert stabilization.wait_until_settled("s", "p", rest, stop, 2.0, _never).waited_s == pytest.approx(2.0)


def test_measures_anyway_past_the_timeout():
    stabilization, bench = _setup(amplitude=lambda t: REST_G if t < 12.0 else 10 * REST_G)
    rest = stabilization.measure_rest("scan-1", _never).vibration_g
    bench.sleep(12.0 - bench.now)
    outcome = stabilization.wait_until_settled("scan-1", "point 0", rest, bench.now, 0.3, _never)
    assert outcome.method == TIMEOUT
    assert outcome.waited_s == pytest.approx(30.0, abs=0.15)


def test_falls_back_to_the_fixed_delay_without_rest_level():
    stabilization, bench = _setup(silent=lambda t: True)
    stop = bench.now
    outcome = stabilization.wait_until_settled("scan-1", "point 0", None, stop, 0.3, _never)
    assert outcome.method == FIXED_DELAY
    assert outcome.waited_s == pytest.approx(0.3)


def test_falls_back_to_the_fixed_delay_when_the_accelerometer_falls_silent_mid_scan():
    # Vibrating and then silent after the stop: without the fallback it would wait the 30 s timeout.
    stabilization, bench = _setup(amplitude=lambda t: REST_G if t < 12.0 else 10 * REST_G,
                                  silent=lambda t: t >= 12.0)
    rest = stabilization.measure_rest("scan-1", _never).vibration_g
    bench.sleep(12.0 - bench.now)
    outcome = stabilization.wait_until_settled("scan-1", "point 0", rest, bench.now, 0.3, _never)
    assert outcome.method == FIXED_DELAY
    assert outcome.waited_s == pytest.approx(1.0)  # one window, already past the fixed delay


def test_a_cancelled_scan_stops_waiting():
    stabilization, bench = _setup(amplitude=lambda t: REST_G if t < 12.0 else 10 * REST_G)
    rest = stabilization.measure_rest("scan-1", _never).vibration_g
    bench.sleep(12.0 - bench.now)
    stop = bench.now
    outcome = stabilization.wait_until_settled("scan-1", "point 0", rest, stop, 0.3, lambda: bench.now > stop + 2.0)
    assert outcome.method == INTERRUPTED
    assert outcome.waited_s < 2.5


def test_samples_without_accelerometer_channel_are_ignored_and_close_unsubscribes():
    bus = InMemoryEventBus()
    stabilization = ColumnStabilization(bus, clock=lambda: 0.5)
    bus.publish(INERTIAL_PROBE_SAMPLE_TOPIC, SimpleNamespace(timestamp_s=0.4, acceleration_g=None))
    assert stabilization.measure_rest("scan-1", _never).vibration_g is None
    stabilization.close()
    bus.publish(INERTIAL_PROBE_SAMPLE_TOPIC, SimpleNamespace(timestamp_s=0.45, acceleration_g=(0, 0, 1)))
    assert stabilization.measure_rest("scan-1", _never).vibration_g is None
