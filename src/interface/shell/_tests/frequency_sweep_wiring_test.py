"""The operator's path, as main.py composes it: the Frequency Sweep panel wired
by the real wiring function, the presenter created in a scope that returns
(like main's composition), garbage collected, then a click on « Lancer ».

Regression: on 2026-11-12 the presenter was referenced only by its service,
the garbage collector deleted it and the button did nothing at the bench."""

import gc

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from application.frequency_sweep.frequency_sweep_service.i_api_frequency_sweep_service import IApiFrequencySweepService
from application.measured_object_registry.measured_object_service.dtos.measured_object_dto import MeasuredObjectDTO
from interface.presenters.frequency_sweep_presenter import FrequencySweepPresenter
from interface.shell.dashboard_wiring import wire_frequency_sweep
from interface.widgets.panels.frequency_sweep_panel import FrequencySweepPanel


class RecordingSweepService(IApiFrequencySweepService):
    """Holds its presenter, like FrequencySweepService (the reference cycle
    the garbage collector collects when nothing else holds the pair)."""

    def __init__(self, received):
        self._received = received
        self._output_port = None

    def set_output_port(self, output_port):
        self._output_port = output_port

    def start_sweep(self, request):
        self._received.append(request)

    def stop_sweep(self):
        self._received.append("stop")


def _compose(panel, received) -> None:
    """Like main.py: the presenter and its service are locals of a function that returns."""
    wire_frequency_sweep(panel, FrequencySweepPresenter(RecordingSweepService(received)))


def _composed_panel(received) -> FrequencySweepPanel:
    QApplication.instance() or QApplication([])
    panel = FrequencySweepPanel()
    _compose(panel, received)
    gc.collect()
    return panel


def test_a_click_on_start_reaches_the_service_after_composition_returned():
    received = []
    panel = _composed_panel(received)
    panel.input_table_height.setText("60")

    QTest.mouseClick(panel.btn_start, Qt.MouseButton.LeftButton)

    (request,) = received
    assert (request.role, request.table_height_mm) == ("instrument_reference", 60.0)
    assert not panel.btn_start.isEnabled()  # running: fields locked until the sweep ends


def test_an_object_measurement_carries_the_chosen_object_and_its_lift_off():
    received = []
    panel = _composed_panel(received)
    selector = panel.measured_object_selector
    selector.set_measured_objects([MeasuredObjectDTO(measured_object_id="obj-1", name="bouteille")])
    selector.activated.emit(selector.findData("obj-1"))  # the operator picks it in the list
    assert not panel.input_lift_off.isEnabled()  # reference role: no object
    panel.combo_role.setCurrentIndex(panel.combo_role.findData("object_measurement"))
    assert panel.input_lift_off.isEnabled()
    panel.input_table_height.setText("60")
    panel.input_lift_off.setText("8")

    QTest.mouseClick(panel.btn_start, Qt.MouseButton.LeftButton)

    (request,) = received
    assert (request.role, request.measured_object_id, request.measured_object_name, request.lift_off_mm) == (
        "object_measurement", "obj-1", "bouteille", 8.0,
    )
