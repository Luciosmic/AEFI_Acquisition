import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from application.services.operator_service.dtos.operator_dto import OperatorDTO

from interface.widgets.panels.scan_control_panel import ScanControlPanel

_ALIVE = []  # keep top-level test widgets alive across tests (Qt still lays them out)


def test_start_carries_the_measured_object_and_the_operator():
    QApplication.instance() or QApplication([])
    panel = ScanControlPanel()
    _ALIVE.append(panel)
    emitted = []
    panel.scan_start_requested.connect(emitted.append)
    panel.input_measured_object.setText("plaque de cuivre 20 mm")
    panel.operator_selector.set_operators([OperatorDTO(operator_id="id-luis", name="Luis")])
    index = panel.operator_selector.findText("Luis")
    panel.operator_selector.setCurrentIndex(index)
    panel.operator_selector.activated.emit(index)

    panel._on_start_clicked()

    assert emitted[0]["measured_object"] == "plaque de cuivre 20 mm"
    assert (emitted[0]["operator_id"], emitted[0]["operator"]) == ("id-luis", "Luis")
