import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from interface.presentation.inertial_sensor_view_model import build_reading_view_model
from interface.widgets.panels.inertial_sensor_panel import InertialSensorPanel


def _make_panel() -> InertialSensorPanel:
    QApplication.instance() or QApplication([])
    return InertialSensorPanel()


def test_labels_and_unverified_banners_are_visible_before_any_value():
    panel = _make_panel()
    assert panel.channel_label_text("accelerometer") == "Accélération (g)"
    assert panel.channel_label_text("lidar") == "Distance lidar (mm)"
    assert panel.unverified_banner_text("accelerometer") == ""
    for key in ("gyroscope", "magnetometer", "lidar"):
        assert "valeur non vérifiée" in panel.unverified_banner_text(key)
    assert "canal provisoire : concept distinct à venir" in panel.note_text("lidar")


def test_buttons_follow_connection_and_acquisition_state():
    panel = _make_panel()
    assert not panel.btn_start.isEnabled() and not panel.btn_stop.isEnabled()

    panel.on_connection_changed(True, "Connecté")
    assert panel.btn_connect.text() == "Déconnecter"
    assert panel.btn_start.isEnabled() and not panel.btn_stop.isEnabled()

    panel.on_acquisition_started()
    assert not panel.btn_start.isEnabled() and panel.btn_stop.isEnabled()

    panel.on_acquisition_stopped()
    assert panel.btn_start.isEnabled() and not panel.btn_stop.isEnabled()

    panel.on_connection_changed(False, "Déconnecté")
    assert panel.btn_connect.text() == "Connecter"
    assert not panel.btn_start.isEnabled()


def test_buttons_emit_requests_and_nothing_fires_by_itself():
    panel = _make_panel()
    received = []
    panel.connect_requested.connect(lambda: received.append("connect"))
    panel.disconnect_requested.connect(lambda: received.append("disconnect"))
    panel.start_requested.connect(lambda: received.append("start"))
    panel.stop_requested.connect(lambda: received.append("stop"))
    assert received == []

    panel.btn_connect.click()
    panel.on_connection_changed(True, "Connecté")
    panel.btn_start.click()
    panel.btn_connect.click()

    assert received == ["connect", "start", "disconnect"]


def test_reading_updates_values_rate_and_count():
    panel = _make_panel()
    panel.on_reading_updated(
        build_reading_view_model(
            acceleration_g=(0.0, 0.0, 1.0),
            angular_rate_dps=(0.1, -0.2, 0.0),
            magnetic_field_ut=(20.0, -5.0, 40.0),
            lidar_distance_mm=1250.0,
            measured_rate_hz=24.96,
            sample_count=120,
        )
    )
    assert panel.value_texts("accelerometer") == ["+0.0000", "+0.0000", "+1.0000"]
    assert panel.value_texts("lidar") == ["1250"]
    assert "25.0 Hz" in panel.lbl_rate.text()
    assert "120" in panel.lbl_rate.text()


def test_failure_shows_reason_and_resets_buttons():
    panel = _make_panel()
    panel.on_connection_changed(True, "Connecté")
    panel.on_acquisition_started()
    panel.on_acquisition_failed("no sample for 3.0 s")
    panel.on_acquisition_stopped()
    assert "no sample for 3.0 s" in panel.lbl_state.text()
    assert panel.btn_start.isEnabled()
