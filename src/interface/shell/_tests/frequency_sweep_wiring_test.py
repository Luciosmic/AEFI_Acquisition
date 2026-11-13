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


def test_a_frequency_list_typed_by_the_operator_reaches_the_service():
    received = []
    panel = _composed_panel(received)
    assert not panel.input_frequency_list.isEnabled()  # per-decade grid by default
    panel.combo_grid.setCurrentIndex(panel.combo_grid.findData("list"))
    assert panel.input_frequency_list.isEnabled() and not panel.spin_points_per_decade.isEnabled()
    panel.input_frequency_list.setText("5e3 ; 200 1000,5")
    assert panel.lbl_frequency_list.text().startswith("3 fréquences lues")
    panel.input_table_height.setText("60")

    QTest.mouseClick(panel.btn_start, Qt.MouseButton.LeftButton)

    (request,) = received
    assert request.frequency_list_hz == (5000.0, 200.0, 1000.5)


def test_an_unreadable_frequency_list_blocks_the_launch_with_its_error():
    received = []
    panel = _composed_panel(received)
    panel.combo_grid.setCurrentIndex(panel.combo_grid.findData("list"))
    panel.input_frequency_list.setText("100 abc")
    panel.input_table_height.setText("60")

    QTest.mouseClick(panel.btn_start, Qt.MouseButton.LeftButton)

    assert received == []
    assert "abc" in panel.lbl_status.text()


def test_a_per_decade_grid_sends_its_density_and_no_list():
    received = []
    panel = _composed_panel(received)
    panel.spin_points_per_decade.setValue(5)
    panel.input_table_height.setText("60")

    QTest.mouseClick(panel.btn_start, Qt.MouseButton.LeftButton)

    (request,) = received
    assert (request.points_per_decade, request.frequency_list_hz) == (5, None)


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
