import time
from typing import List

import pytest

from application.services.inertial_sensor_service.dtos.inertial_sensor_dtos import (
    InertialSensorAcquisitionConfig,
)
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.execution.inertial_sensor_acquisition_executor import (
    SAMPLE_ACQUIRED_TOPIC,
    STREAM_FAILED_TOPIC,
    InertialSensorAcquisitionExecutor,
)
from infrastructure.hardware.lsm9ds1.fake.fake_inertial_sensor_stream_adapter import (
    FakeInertialSensorStreamAdapter,
)

CONFIG = InertialSensorAcquisitionConfig(channels=("accelerometer", "lidar"))


def _wait_for(predicate, timeout_s=3.0):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.005)
    return False


class _Setup:
    def __init__(self, port):
        self.port = port
        self.port.connect()
        self.bus = InMemoryEventBus()
        self.samples: List = []
        self.failures: List = []
        self.bus.subscribe(SAMPLE_ACQUIRED_TOPIC, self.samples.append)
        self.bus.subscribe(STREAM_FAILED_TOPIC, self.failures.append)
        self.executor = InertialSensorAcquisitionExecutor(self.bus)

    def close(self):
        self.executor.stop()


@pytest.fixture
def setup():
    s = _Setup(FakeInertialSensorStreamAdapter(realtime=False))
    yield s
    s.close()


def test_publishes_indexed_samples_with_one_acquisition_id(setup):
    setup.executor.start(CONFIG, setup.port)
    assert _wait_for(lambda: len(setup.samples) >= 5)
    setup.executor.stop()

    first, second = setup.samples[0], setup.samples[1]
    assert (first.sample_index, second.sample_index) == (0, 1)
    assert first.acquisition_id == second.acquisition_id
    assert first.acceleration_g == (0.0, 0.0, 1.0)
    assert first.lidar_distance_mm is not None
    assert first.angular_rate_dps is None
    assert setup.failures == []


def test_stop_sends_stream_stop_to_the_port_and_clears_running(setup):
    calls = []
    original = setup.port.stop_stream
    setup.port.stop_stream = lambda: (calls.append("stop_stream"), original())[1]

    setup.executor.start(CONFIG, setup.port)
    assert _wait_for(lambda: len(setup.samples) >= 1)
    assert setup.executor.is_running()
    setup.executor.stop()

    assert not setup.executor.is_running()
    assert calls == ["stop_stream"]
    assert setup.failures == []  # an operator stop is not a failure


def test_start_while_running_is_ignored(setup):
    setup.executor.start(CONFIG, setup.port)
    thread = setup.executor._thread
    setup.executor.start(CONFIG, setup.port)
    assert setup.executor._thread is thread
    setup.executor.stop()


def test_read_errors_beyond_tolerance_publish_one_failure_and_still_stop_the_stream():
    s = _Setup(FakeInertialSensorStreamAdapter(realtime=False, fail_after_samples=3))
    try:
        s.executor.start(CONFIG, s.port)
        assert _wait_for(lambda: len(s.failures) == 1)
        assert _wait_for(lambda: not s.executor.is_running())
        assert len(s.samples) == 3
        assert "simulated serial read failure" in s.failures[0].reason
        assert s.failures[0].acquisition_id == s.samples[0].acquisition_id
    finally:
        s.close()


def test_silent_board_publishes_failure_after_max_silence(monkeypatch):
    monkeypatch.setattr(InertialSensorAcquisitionExecutor, "MAX_SILENCE_S", 0.1)
    monkeypatch.setattr(InertialSensorAcquisitionExecutor, "READ_TIMEOUT_S", 0.02)
    s = _Setup(FakeInertialSensorStreamAdapter(realtime=True, stall_after_samples=2))
    try:
        s.executor.start(CONFIG, s.port)
        assert _wait_for(lambda: len(s.failures) == 1)
        assert "no sample" in s.failures[0].reason
    finally:
        s.close()


def test_start_stream_failure_publishes_failure_without_samples():
    class RefusingPort(FakeInertialSensorStreamAdapter):
        def start_stream(self, channels):
            raise OSError("COM5 write timeout")

    s = _Setup(RefusingPort(realtime=False))
    try:
        s.executor.start(CONFIG, s.port)
        assert _wait_for(lambda: len(s.failures) == 1)
        assert s.samples == []
        assert "COM5 write timeout" in s.failures[0].reason
    finally:
        s.close()


def test_restart_gets_a_new_acquisition_id(setup):
    setup.executor.start(CONFIG, setup.port)
    assert _wait_for(lambda: len(setup.samples) >= 1)
    setup.executor.stop()
    first_id = setup.samples[0].acquisition_id

    setup.samples.clear()
    setup.executor.start(CONFIG, setup.port)
    assert _wait_for(lambda: len(setup.samples) >= 1)
    setup.executor.stop()

    assert setup.samples[0].acquisition_id != first_id
    assert setup.samples[0].sample_index == 0
