import os
from uuid import uuid4

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QCoreApplication

from application.services.inertial_sensor_service.inertial_sensor_service import InertialSensorService
from domain.inertial_sensor.events.inertial_sensor_connection_changed.inertial_sensor_connection_changed import (
    InertialSensorConnectionChanged,
)
from domain.inertial_sensor.events.inertial_sensor_sample_acquired.inertial_sensor_sample_acquired import (
    InertialSensorSampleAcquired,
)
from domain.inertial_sensor.events.inertial_sensor_stream_failed.inertial_sensor_stream_failed import (
    InertialSensorStreamFailed,
)
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.hardware.lsm9ds1.fake.fake_inertial_sensor_stream_adapter import (
    FakeInertialSensorStreamAdapter,
)
from infrastructure.mocks.adapter_mock_i_inertial_sensor_acquisition_executor import (
    MockInertialSensorAcquisitionExecutor,
)
from interface.presenters.inertial_sensor_presenter import InertialSensorPresenter


@pytest.fixture(scope="module", autouse=True)
def qt_app():
    return QCoreApplication.instance() or QCoreApplication([])


class Rig:
    def __init__(self, port=None):
        self.bus = InMemoryEventBus()
        self.executor = MockInertialSensorAcquisitionExecutor()
        self.port = port or FakeInertialSensorStreamAdapter(realtime=False)
        self.service = InertialSensorService(self.executor, self.port, self.bus)
        self.presenter = InertialSensorPresenter(self.service, self.bus)
        self.connections, self.readings, self.failures = [], [], []
        self.started, self.stopped = [], []
        self.presenter.connection_changed.connect(lambda c, label: self.connections.append((c, label)))
        self.presenter.reading_updated.connect(self.readings.append)
        self.presenter.acquisition_failed.connect(self.failures.append)
        self.presenter.acquisition_started.connect(lambda: self.started.append(True))
        self.presenter.acquisition_stopped.connect(lambda: self.stopped.append(True))
        self.acquisition_id = uuid4()

    def publish_sample(self, index, timestamp_s, **channels):
        self.bus.publish(
            "inertialsensorsampleacquired",
            InertialSensorSampleAcquired(
                acquisition_id=self.acquisition_id,
                sample_index=index,
                timestamp_s=timestamp_s,
                **channels,
            ),
        )


def test_connect_request_calls_service_and_reports_connection():
    rig = Rig()
    rig.presenter.on_connect_requested()
    assert rig.port.is_connected()
    assert rig.connections == [(True, "Connecté")]


def test_connection_failure_is_reported_with_the_error_text():
    rig = Rig(port=FakeInertialSensorStreamAdapter(simulate_connection_failure=True))
    rig.presenter.on_connect_requested()
    assert rig.connections[-1][0] is False
    assert "timeout" in rig.connections[-1][1]


def test_start_request_signals_started_only_when_service_runs():
    rig = Rig()
    rig.presenter.on_start_requested()  # not connected: service refuses
    assert rig.started == []
    rig.presenter.on_connect_requested()
    rig.presenter.on_start_requested()
    assert rig.started == [True]
    rig.presenter.on_stop_requested()


def test_display_keeps_only_the_latest_sample_between_refreshes():
    rig = Rig()
    rig.presenter.on_connect_requested()
    rig.presenter.on_start_requested()
    for k in range(25):
        rig.publish_sample(k, k * 0.04, acceleration_g=(0.0, 0.0, 1.0 + k))
    assert rig.readings == []  # nothing emitted per sample

    rig.presenter.refresh_display()

    assert len(rig.readings) == 1
    accelerometer = rig.readings[0].channels[0]
    assert accelerometer.values == ("+0.0000", "+0.0000", "+25.0000")  # latest sample kept
    assert rig.readings[0].sample_count == 25
    rig.presenter.on_stop_requested()


def test_refresh_without_new_sample_emits_nothing():
    rig = Rig()
    rig.presenter.on_connect_requested()
    rig.presenter.on_start_requested()
    rig.publish_sample(0, 0.0, acceleration_g=(0.0, 0.0, 1.0))
    rig.presenter.refresh_display()
    rig.presenter.refresh_display()
    assert len(rig.readings) == 1
    rig.presenter.on_stop_requested()


def test_measured_rate_comes_from_sample_timestamps():
    rig = Rig()
    rig.presenter.on_connect_requested()
    rig.presenter.on_start_requested()
    for k in range(26):
        rig.publish_sample(k, 100.0 + k * 0.04, acceleration_g=(0.0, 0.0, 1.0))
    rig.presenter.refresh_display()
    assert rig.readings[-1].measured_rate_hz == pytest.approx(25.0)
    rig.presenter.on_stop_requested()


def test_stream_failure_is_reported_and_ends_the_acquisition_state():
    rig = Rig()
    rig.presenter.on_connect_requested()
    rig.presenter.on_start_requested()
    rig.bus.publish(
        "inertialsensorstreamfailed",
        InertialSensorStreamFailed(acquisition_id=rig.acquisition_id, reason="no sample for 3.0 s"),
    )
    assert rig.failures == ["no sample for 3.0 s"]
    assert rig.stopped == [True]
    assert not rig.presenter.is_display_timer_active


def test_stop_request_stops_service_and_display_timer():
    rig = Rig()
    rig.presenter.on_connect_requested()
    rig.presenter.on_start_requested()
    assert rig.presenter.is_display_timer_active
    rig.presenter.on_stop_requested()
    assert rig.executor.stop_calls == 1
    assert rig.stopped == [True]
    assert not rig.presenter.is_display_timer_active


def test_disconnect_request_ends_acquisition_state_and_reports_disconnected():
    rig = Rig()
    rig.presenter.on_connect_requested()
    rig.presenter.on_start_requested()
    rig.presenter.on_disconnect_requested()
    assert rig.connections[-1] == (False, "Déconnecté")
    assert rig.stopped == [True]
    assert not rig.presenter.is_display_timer_active


def test_late_connection_event_after_shutdown_is_ignored():
    rig = Rig()
    rig.presenter.shutdown()
    rig.bus.publish("inertialsensorconnectionchanged", InertialSensorConnectionChanged(connected=True))
    assert rig.connections == []
