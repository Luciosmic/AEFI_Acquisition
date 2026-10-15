from typing import List

import pytest

from application.services.inertial_sensor_service.inertial_sensor_service import (
    CONNECTION_CHANGED_TOPIC,
    InertialSensorService,
)
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.hardware.lsm9ds1.fake.fake_inertial_sensor_stream_adapter import (
    FakeInertialSensorStreamAdapter,
)
from infrastructure.mocks.adapter_mock_i_inertial_sensor_acquisition_executor import (
    MockInertialSensorAcquisitionExecutor,
)


class _Recorder:
    def __init__(self, bus: InMemoryEventBus, topic: str) -> None:
        self.events: List = []
        bus.subscribe(topic, self.events.append)


@pytest.fixture
def bus():
    return InMemoryEventBus()


def make_service(bus, port=None, channels=("accelerometer", "lidar")):
    port = port or FakeInertialSensorStreamAdapter(realtime=False)
    executor = MockInertialSensorAcquisitionExecutor()
    service = InertialSensorService(executor, port, bus, channels=channels)
    return service, port, executor


def test_connect_publishes_connected_event(bus):
    connections = _Recorder(bus, CONNECTION_CHANGED_TOPIC)
    service, port, _ = make_service(bus)

    service.connect_sensor()

    assert port.is_connected()
    assert len(connections.events) == 1
    assert connections.events[0].connected is True
    assert connections.events[0].error is None


def test_connect_failure_publishes_event_without_raising(bus):
    connections = _Recorder(bus, CONNECTION_CHANGED_TOPIC)
    service, _, _ = make_service(
        bus, port=FakeInertialSensorStreamAdapter(simulate_connection_failure=True)
    )

    service.connect_sensor()

    assert len(connections.events) == 1
    assert connections.events[0].connected is False
    assert "timeout" in connections.events[0].error


def test_connect_twice_is_idempotent_and_publishes_once(bus):
    connections = _Recorder(bus, CONNECTION_CHANGED_TOPIC)
    service, _, _ = make_service(bus)

    service.connect_sensor()
    service.connect_sensor()

    assert len(connections.events) == 1


def test_start_acquisition_delegates_configured_channels_and_port_to_executor(bus):
    service, port, executor = make_service(bus, channels=("accelerometer", "lidar"))
    service.connect_sensor()

    service.start_acquisition()

    assert [c.channels for c in executor.started_configs] == [("accelerometer", "lidar")]
    assert executor.stream_port is port
    assert service.is_acquisition_running()


def test_start_acquisition_when_not_connected_does_nothing(bus):
    service, _, executor = make_service(bus)

    service.start_acquisition()

    assert executor.started_configs == []
    assert not service.is_acquisition_running()


def test_start_acquisition_twice_starts_only_once(bus):
    service, _, executor = make_service(bus)
    service.connect_sensor()

    service.start_acquisition()
    service.start_acquisition()

    assert len(executor.started_configs) == 1


def test_disconnect_stops_acquisition_then_closes_the_link_and_publishes(bus):
    connections = _Recorder(bus, CONNECTION_CHANGED_TOPIC)
    service, port, executor = make_service(bus)
    service.connect_sensor()
    service.start_acquisition()

    service.disconnect_sensor()

    assert executor.stop_calls == 1
    assert not port.is_connected()
    assert [e.connected for e in connections.events] == [True, False]


def test_shutdown_stops_acquisition_and_disconnects_even_when_port_raises(bus):
    class ExplodingPort(FakeInertialSensorStreamAdapter):
        def disconnect(self):
            raise OSError("serial port vanished")

    service, _, executor = make_service(bus, port=ExplodingPort(realtime=False))
    service.connect_sensor()
    service.start_acquisition()

    service.shutdown()  # must not raise

    assert executor.stop_calls == 1


def test_shutdown_disconnects_the_port_which_sends_the_stream_stop(bus):
    calls = []

    class SpyPort(FakeInertialSensorStreamAdapter):
        def disconnect(self):
            calls.append("disconnect")
            super().disconnect()

    service, port, _ = make_service(bus, port=SpyPort(realtime=False))
    service.connect_sensor()

    service.shutdown()

    assert calls == ["disconnect"]
    assert not port.is_connected()
