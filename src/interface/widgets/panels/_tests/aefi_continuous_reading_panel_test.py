import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from application.services.operator_service.dtos.operator_dto import OperatorDTO

from interface.widgets.panels.aefi_continuous_reading_panel import AefiContinuousReadingPanel

_ALIVE = []  # keep top-level test widgets alive across tests (Qt still lays them out)


def _panel():
    QApplication.instance() or QApplication([])
    panel = AefiContinuousReadingPanel()
    _ALIVE.append(panel)
    return panel


def test_controlled_stream_locks_start_and_stop_even_when_its_owner_stops_it():
    panel = _panel()

    panel.set_acquisition_controller("caractérisation débit MCU", True)
    panel.on_acquisition_stopped("acq-1")  # the owner stops the stream it started

    assert not panel.btn_start.isEnabled()
    assert not panel.btn_stop.isEnabled()
    assert "caractérisation débit MCU" in panel.lbl_status.toolTip()


def test_released_stream_follows_the_running_state():
    panel = _panel()
    panel.set_acquisition_controller("scan", True)

    panel.set_acquisition_controller("", True)
    assert not panel.btn_start.isEnabled()
    assert panel.btn_stop.isEnabled()

    panel.set_acquisition_controller("", False)
    assert panel.btn_start.isEnabled()
    assert not panel.btn_stop.isEnabled()


def test_start_carries_the_measured_object_and_the_operator():
    panel = _panel()
    emitted = []
    panel.acquisition_start_requested.connect(emitted.append)
    panel.input_measured_object.setText("bouteille d'eau, 8 mm")
    panel.operator_selector.set_operators([OperatorDTO(operator_id="id-luis", name="Luis")])
    index = panel.operator_selector.findText("Luis")
    panel.operator_selector.setCurrentIndex(index)
    panel.operator_selector.activated.emit(index)

    panel._on_start_clicked()

    assert emitted[0]["measured_object"] == "bouteille d'eau, 8 mm"
    assert (emitted[0]["operator_id"], emitted[0]["operator"]) == ("id-luis", "Luis")
