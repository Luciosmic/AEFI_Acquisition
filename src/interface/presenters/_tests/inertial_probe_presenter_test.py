import os
from uuid import uuid4

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from application.inertial_probe.inertial_probe_service.inertial_probe_service import InertialProbeService
from domain.inertial_probe.events.inertial_probe_connection_changed.inertial_probe_connection_changed import (
    InertialProbeConnectionChanged,
)
from domain.inertial_probe.events.inertial_probe_sample_acquired.inertial_probe_sample_acquired import (
    InertialProbeSampleAcquired,
)
from domain.inertial_probe.events.inertial_probe_stream_failed.inertial_probe_stream_failed import (
    InertialProbeStreamFailed,
)
from domain.lidar.lidar_distance.lidar_distance import LidarDistance
from infrastructure.in_memory_event_bus.in_memory_event_bus import InMemoryEventBus
from infrastructure.hardware.lsm9ds1.adapter_inertial_probe_stream_port.fake.fake_adapter_inertial_probe_stream_port import (
    FakeInertialProbeStreamAdapter,
)
from infrastructure.mocks.adapter_mock_i_inertial_probe_acquisition_executor import (
    MockInertialProbeAcquisitionExecutor,
)
from interface.presenters.inertial_probe_presenter import InertialProbePresenter


@pytest.fixture(scope="module", autouse=True)
def qt_app():
    # QApplication, not QCoreApplication: a later test module that builds widgets
    # would otherwise reuse a core-only instance and crash the interpreter.
    return QApplication.instance() or QApplication([])


class Rig:
    def __init__(self, port=None):
        self.bus = InMemoryEventBus()
        self.executor = MockInertialProbeAcquisitionExecutor()
        self.port = port or FakeInertialProbeStreamAdapter(realtime=False)
        self.service = InertialProbeService(self.executor, self.port, self.bus)
        self.presenter = InertialProbePresenter(self.service, self.bus)
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
            "inertialprobesampleacquired",
            InertialProbeSampleAcquired(
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
    rig = Rig(port=FakeInertialProbeStreamAdapter(simulate_connection_failure=True))
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


def test_lidar_zero_is_displayed_as_no_return():
    rig = Rig()
    rig.presenter.on_connect_requested()
    rig.presenter.on_start_requested()
    rig.publish_sample(0, 0.0, lidar_distance=LidarDistance.from_raw(0, 1.0))
    rig.presenter.refresh_display()
    lidar = next(c for c in rig.readings[0].channels if c.key == "lidar")
    assert lidar.values == ("pas de retour",)
    rig.publish_sample(1, 0.04, lidar_distance=LidarDistance.from_raw(1250, 1.0))
    rig.presenter.refresh_display()
    assert next(c for c in rig.readings[1].channels if c.key == "lidar").values == ("1250",)
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
        "inertialprobestreamfailed",
        InertialProbeStreamFailed(acquisition_id=rig.acquisition_id, reason="no sample for 3.0 s"),
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
    rig.bus.publish("inertialprobeconnectionchanged", InertialProbeConnectionChanged(connected=True))
    assert rig.connections == []


def test_open_at_startup_connects_and_starts_like_the_panel_buttons():
    rig = Rig()
    rig.presenter.open_at_startup()
    assert rig.port.is_connected()
    assert rig.service.is_acquisition_running()
    assert rig.connections == [(True, "Connecté")]
    assert rig.started == [True]
    assert rig.presenter.is_display_timer_active


def test_open_at_startup_without_board_leaves_the_error_and_does_not_start():
    rig = Rig(port=FakeInertialProbeStreamAdapter(simulate_connection_failure=True))
    rig.presenter.open_at_startup()
    assert rig.connections[-1][0] is False
    assert not rig.service.is_acquisition_running()
    assert rig.started == []
