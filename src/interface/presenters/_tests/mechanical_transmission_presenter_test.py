"""MechanicalTransmissionPresenter + MechanicalTransmissionPanel: current transmission, saving, scan lock."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from datetime import datetime, timezone

from PySide6.QtWidgets import QApplication

from application.services.mechanical_transmission_calibration_service.dtos.mechanical_transmission_calibration_dto import (
    MechanicalTransmissionCalibrationDTO,
)
from application.services.mechanical_transmission_calibration_service.dtos.mechanical_transmission_gap_dto import (
    MechanicalTransmissionGapDTO,
)
from infrastructure.in_memory_event_bus.in_memory_event_bus import InMemoryEventBus
from interface.presenters.mechanical_transmission_presenter import MechanicalTransmissionPresenter
from interface.widgets.panels.mechanical_transmission_panel import MechanicalTransmissionPanel

CURRENT = MechanicalTransmissionCalibrationDTO(
    motor_name="IGUS-S-AN-060-035-060",
    stepper_driver_name="TB6600",
    microsteps=16,
    driver_current_a=3.5,
    driver_peak_current_a=4.0,
    microns_per_pulse=20.62,
    driver_current_warning="Driver current 3.5 A (4.0 A peak) below motor rated current 4.2 A",
    recorded_at=datetime(2026, 11, 10, 16, 0, tzinfo=timezone.utc),
)
GAP = MechanicalTransmissionGapDTO("IGUS", "réglage de la transmission mécanique", "panneau Calibration")


class _Service:
    def __init__(self, current=CURRENT):
        self.current = current
        self.recorded = []
        self.refusal = None

    def get_current_calibration(self):
        return self.current

    def get_current_gap(self):
        return None if self.current else GAP

    def record_calibration(self, microsteps, driver_current_a, driver_peak_current_a, microns_per_pulse):
        if self.refusal:
            raise ValueError(self.refusal)
        self.recorded.append((microsteps, driver_current_a, driver_peak_current_a, microns_per_pulse))


def _setup(service=None):
    QApplication.instance() or QApplication([])
    service = service or _Service()
    bus = InMemoryEventBus()
    presenter = MechanicalTransmissionPresenter(service, bus)
    panel = MechanicalTransmissionPanel()
    presenter.transmission_changed.connect(panel.show_transmission)
    presenter.status_message.connect(panel.set_status_message)
    presenter.scan_running_changed.connect(panel.set_scan_running)
    panel.save_requested.connect(presenter.on_save_requested)
    return service, bus, presenter, panel


def test_current_transmission_is_shown_and_prefills_the_form():
    _service, _bus, presenter, panel = _setup()

    presenter.refresh_state()

    assert "20,62 µm par incrément" in panel.lbl_headline.text()
    assert "1/16" in panel.lbl_headline.text()
    assert "TB6600" in panel.lbl_detail.text()
    assert "below motor rated current" in panel.lbl_warning.text()
    assert (panel.spin_microns.value(), panel.spin_microsteps.value()) == (20.62, 16)
    assert (panel.spin_current.value(), panel.spin_peak.value()) == (3.5, 4.0)


def test_nothing_recorded_says_what_is_missing_and_keeps_the_form_as_is():
    _service, _bus, presenter, panel = _setup(_Service(current=None))

    presenter.refresh_state()

    assert "Aucune transmission" in panel.lbl_headline.text()
    assert "réglage de la transmission mécanique" in panel.lbl_detail.text()
    assert not panel.lbl_warning.isVisibleTo(panel)


def test_save_sends_the_form_to_the_service_and_confirms():
    service, _bus, _presenter, panel = _setup()
    panel.spin_microns.setValue(20.5)

    panel.btn_save.click()

    assert service.recorded == [(16, 3.5, 4.0, 20.5)]
    assert "20,5 µm par incrément" in panel.lbl_status.text()


def test_domain_refusal_is_shown_not_raised():
    service, _bus, _presenter, panel = _setup()
    service.refusal = "driver_peak_current_a (3.0) must be >= driver_current_a (3.5)"

    panel.btn_save.click()

    assert service.recorded == []
    assert panel.lbl_status.text().startswith("Erreur:") and "driver_peak_current_a" in panel.lbl_status.text()


def test_a_new_entry_refreshes_the_displayed_transmission():
    service, bus, _presenter, panel = _setup()

    service.current = MechanicalTransmissionCalibrationDTO(
        **{**CURRENT.__dict__, "microns_per_pulse": 21.46, "driver_current_warning": None}
    )
    bus.publish("mechanicaltransmissioncalibrationentryadded", object())

    assert "21,46 µm par incrément" in panel.lbl_headline.text()
    assert not panel.lbl_warning.isVisibleTo(panel)


def test_saving_is_locked_during_a_scan_and_back_after_it():
    service, bus, _presenter, panel = _setup()

    bus.publish("scanstarted", object())
    assert not panel.btn_save.isEnabled()
    panel.save_requested.emit(16, 3.5, 4.0, 20.0)  # even if the button was bypassed
    assert service.recorded == []
    assert "scan est en cours" in panel.lbl_status.text()

    bus.publish("scancompleted", object())
    assert panel.btn_save.isEnabled()
    panel.btn_save.click()
    assert len(service.recorded) == 1


def test_the_calibration_panel_hosts_the_transmission_tab():
    from interface.widgets.panels.calibration_panel import CalibrationPanel

    QApplication.instance() or QApplication([])
    panel = CalibrationPanel()

    tabs = [panel._tabs.tabText(i) for i in range(panel._tabs.count())]
    assert "Mouvement" in tabs
    group = panel._tabs.widget(tabs.index("Mouvement"))
    assert group.widget(group.count() - 1) is panel.mechanical_transmission_panel


def test_components_are_grouped_under_mouvement_and_electronique():
    from types import SimpleNamespace

    from interface.widgets.panels.calibration_panel import CalibrationPanel

    QApplication.instance() or QApplication([])
    panel = CalibrationPanel()

    def kind(key, label):
        return SimpleNamespace(key=key, label=label, quantities=())

    for key, label in (
        ("conditioning_electronics_board", "Carte de conditionnement"),
        ("adc", "ADC"),
        ("motors", "Moteurs"),
        ("stepper_driver", "Driver pas à pas"),
    ):
        panel.add_hardware_component_tab(kind(key, label))

    def labels(tabs):
        return [tabs.tabText(i) for i in range(tabs.count())]

    top = labels(panel._tabs)
    assert top == ["Calibration capteur", "Géométrie source", "Mouvement", "Électronique"]
    motion = panel._tabs.widget(top.index("Mouvement"))
    electronics = panel._tabs.widget(top.index("Électronique"))
    assert labels(motion) == ["Moteurs", "Driver pas à pas", "Transmission"]
    assert labels(electronics) == ["Carte de conditionnement", "ADC"]
