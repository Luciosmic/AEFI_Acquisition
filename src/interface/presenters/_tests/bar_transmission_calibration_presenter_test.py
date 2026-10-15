import os
from datetime import datetime, timezone
from uuid import uuid4

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from application.services.bar_transmission_calibration_service.dtos.bar_transmission_calibration_dtos import (
    AxisBarTransmissionDTO,
    BarCalibrationSettingsDTO,
    BarTransmissionMeanDTO,
    CoarseLocalizationDTO,
    EdgeBracketDTO,
    FrontBracketDTO,
    ProfilePointDTO,
    RestPointDTO,
)
from application.services.bar_transmission_calibration_service.errors.bar_transmission_calibration_error import (
    BarNotFound,
    BenchResourceControlled,
)
from domain.shared_kernel.events.motor_increments_updated.motor_increments_updated import MotorIncrementsUpdated
from domain.shared_kernel.operation_result import OperationResult
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from interface.presenters.bar_transmission_calibration_presenter import BarTransmissionCalibrationPresenter
from interface.widgets.panels.bar_transmission_calibration_panel import BarTransmissionCalibrationPanel


# Module-level reference: the application must outlive the widgets built below.
_APP = QApplication.instance() or QApplication([])


def axis_dto(axis, travel=69.76):
    bracket = EdgeBracketDTO(1001, 1000, False, 1000.5, 0.5)
    return AxisBarTransmissionDTO(
        axis=axis, bar_length_mm=500.0, bar_length_uncertainty_mm=0.0, first_front=bracket,
        second_front=EdgeBracketDTO(23_936, 23_937, True, 23_936.5, 0.5), full_steps_per_revolution=200,
        microsteps=16, increments_between_fronts=22_936.0, increments_uncertainty=1.0,
        travel_per_motor_revolution_mm=travel, travel_per_motor_revolution_uncertainty_mm=0.003,
        relative_uncertainty=4.4e-5, microns_per_pulse=21.8, on_bar_distance_mm=250.0,
        off_bar_distance_mm=1250.0, threshold_mm=750.0, plateau_noise_mm=2.0,
        measured_at=datetime.now(timezone.utc),
    )


MEAN = BarTransmissionMeanDTO(69.76, 69.70, 69.73, 0.003, 0.06, 8.6e-4, False)


class StubService:
    def __init__(self):
        self.output_port = None
        self.measure_result = OperationResult.ok(None)
        self.recorded = []

    def set_output_port(self, port):
        self.output_port = port

    def default_settings(self):
        return BarCalibrationSettingsDTO()

    def measure_axis(self, axis, length, length_uncertainty, settings):
        self.measured_with = (axis, length, length_uncertainty, settings)
        return self.measure_result

    def cancel_measurement(self):
        pass

    def compare(self, x, y):
        return OperationResult.ok(MEAN)

    def record(self, x, y):
        self.recorded.append((x.axis, y.axis))
        return OperationResult.ok(BarTransmissionMeanDTO(**{**MEAN.__dict__, "entry_id": uuid4()}))


# Rigs live until the interpreter exits, as in the app: garbage-collecting a rig between
# tests made the pytest process end in an access violation (not reproduced outside pytest).
_RIGS = []


class Rig:
    def __init__(self):
        _RIGS.append(self)
        self.bus = InMemoryEventBus()
        self.service = StubService()
        self.presenter = BarTransmissionCalibrationPresenter(self.service, self.bus)
        self.panel = BarTransmissionCalibrationPanel()
        p, w = self.presenter, self.panel
        w.measure_requested.connect(p.on_measure_requested)
        w.record_requested.connect(p.on_record_requested)
        p.increments_updated.connect(w.on_increments_updated)
        p.running_changed.connect(w.set_running)
        p.progress_message.connect(w.append_progress)
        p.axis_result_updated.connect(w.on_axis_result)
        p.mean_updated.connect(w.on_mean)
        p.status_message.connect(w.set_status_message)
        p.plot_reset.connect(w.reset_plot)
        p.profile_points_added.connect(w.add_profile_points)
        p.coarse_localization_shown.connect(w.show_coarse_localization)
        p.rest_point_added.connect(w.add_rest_point)
        p.front_bracket_updated.connect(w.show_front_bracket)


def test_registers_as_output_port_and_relays_increments():
    rig = Rig()
    assert rig.service.output_port is rig.presenter
    rig.bus.publish("motorincrementsupdated", MotorIncrementsUpdated(x_increments=1234, y_increments=-5, is_moving=True))
    assert rig.panel.lbl_x_increments.text() == "1234"
    assert rig.panel.lbl_y_increments.text() == "-5"


def test_measure_sends_axis_and_length_with_default_settings_and_locks_the_tab():
    rig = Rig()
    rig.panel.combo_axis.setCurrentText("Y")
    rig.panel.spin_bar_length.setValue(487.25)
    rig.panel.btn_measure.click()
    assert rig.service.measured_with == ("Y", 487.25, 0.0, BarCalibrationSettingsDTO())
    assert not rig.panel.btn_measure.isEnabled()
    assert rig.panel.btn_cancel.isEnabled()


def test_refusal_is_shown_in_clear_and_the_tab_stays_usable():
    rig = Rig()
    rig.service.measure_result = OperationResult.fail(BenchResourceControlled("moteurs du banc sous le contrôle de : scan"))
    rig.panel.btn_measure.click()
    assert "scan" in rig.panel.lbl_status.text()
    assert rig.panel.btn_measure.isEnabled()


def test_failure_from_the_measurement_is_shown():
    rig = Rig()
    rig.presenter.present_axis_failed("X", BarNotFound("X", "pas de créneau"))
    assert "pas de créneau" in rig.panel.lbl_status.text()


def test_record_needs_both_axes_then_shows_mean_and_deviation():
    rig = Rig()
    rig.presenter.present_axis_measured(axis_dto("X"))
    assert "N = 22936.0 ± 1.0" in rig.panel.lbl_result["X"].text()
    assert "69.76000" in rig.panel.lbl_result["X"].text()
    rig.panel.btn_record.click()
    assert rig.service.recorded == []
    assert "Y" in rig.panel.lbl_status.text()

    rig.presenter.present_axis_measured(axis_dto("Y", 69.70))
    assert "écart X−Y" in rig.panel.lbl_mean.text()
    rig.panel.btn_record.click()
    assert rig.service.recorded == [("X", "Y")]
    assert "enregistrée" in rig.panel.lbl_status.text()


def test_live_plot_shows_profile_no_return_threshold_fronts_points_and_brackets():
    rig = Rig()
    p, w = rig.presenter, rig.panel
    p.present_profile_points("X", [ProfilePointDTO(10.0, 1250.0), ProfilePointDTO(42.0, None)])
    p.present_profile_points("X", [ProfilePointDTO(2_000.0, 250.0)])
    p.present_coarse_localization("X", CoarseLocalizationDTO(250.0, 1250.0, 750.0, 1_990.0, 6_010.0))
    p.present_rest_point("X", RestPointDTO(2_100, 251.0, 1.5, 10, 10, "on_bar"))
    p.present_rest_point("X", RestPointDTO(1_600, None, None, 0, 40, "off_bar"))
    p.present_front_bracket("X", FrontBracketDTO("front 1", 2_100, 1_600))
    w.redraw_plot_if_needed()
    labels = w.figure.axes[0].get_legend_handles_labels()[1]
    assert {"fly scan", "pas de retour", "seuil", "sur la barre", "hors barre"} <= set(labels)
    assert w._profile == [(10.0, 1250.0), (42.0, None), (2_000.0, 250.0)]
    assert w._threshold_mm == 750.0 and w._coarse_fronts == (1_990.0, 6_010.0)
    assert w._brackets == {"front 1": (2_100, 1_600)}


def test_plot_is_redrawn_only_when_data_changed_and_reset_at_each_measurement():
    rig = Rig()
    w = rig.panel
    rig.presenter.present_profile_points("X", [ProfilePointDTO(10.0, 1250.0)])
    w.redraw_plot_if_needed()
    first = w.figure.axes[0]
    w.redraw_plot_if_needed()
    assert w.figure.axes[0] is first  # nothing new: no redraw
    rig.panel.btn_measure.click()
    assert w._profile == [] and w._brackets == {} and w._threshold_mm is None
