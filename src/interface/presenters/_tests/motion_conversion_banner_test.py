"""Calibration state -> banner view model: MotionPresenter and ScanPresenter relay what is missing, panels block."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from application.services.motion_control_service.dtos.motion_conversion_status_dto import MotionConversionStatusDTO
from application.services.scan_application_service.errors.scan_start_error import ScanRefusedBenchNotCalibrated
from domain.shared_kernel.motion.events.motion_conversion_became_available.motion_conversion_became_available import (
    MotionConversionBecameAvailable,
)
from domain.shared_kernel.motion.events.motion_conversion_found_missing.motion_conversion_found_missing import (
    MotionConversionFoundMissing,
)
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from interface.presenters.motion_presenter import MotionPresenter
from interface.presenters.scan_presenter import ScanPresenter
from interface.widgets.panels.motion_panel_compact import MotionPanelCompact
from interface.widgets.panels.scan_control_panel import ScanControlPanel

MISSING = MotionConversionStatusDTO(
    is_available=False, motor_name="IGUS-S-AN-060-035-060", missing_quantity="µm par impulsion",
    where_to_enter="panneau Calibration, onglet « Moteurs »",
)


class _MotionService:
    def __init__(self):
        self.status = MISSING

    limits = (1270.0, 1270.0)

    def get_axis_limits(self):
        return self.limits

    def get_conversion_status(self):
        return self.status


class _ScanService:
    def __init__(self):
        self.refusal = ScanRefusedBenchNotCalibrated("IGUS", "µm par impulsion", "onglet Moteurs")

    def set_output_port(self, port):
        pass

    def get_start_refusal(self):
        return self.refusal

    def execute_scan(self, dto):
        return False

    def execute_line_scan(self, dto):
        return False


class _Export:
    def configure_export(self, dto):
        pass


def _app():
    return QApplication.instance() or QApplication([])


def test_motion_presenter_publishes_the_missing_quantity_at_initialization():
    _app()
    presenter = MotionPresenter(_MotionService(), InMemoryEventBus())
    banners = []
    presenter.conversion_banner_changed.connect(banners.append)

    presenter.initialize()

    assert banners[-1].visible
    assert "µm par impulsion" in banners[-1].text
    assert "IGUS-S-AN-060-035-060" in banners[-1].text
    assert "Moteurs" in banners[-1].text


def test_motion_presenter_clears_the_banner_when_the_conversion_becomes_available():
    _app()
    bus = InMemoryEventBus()
    service = _MotionService()
    presenter = MotionPresenter(service, bus)
    presenter.initialize()
    banners = []
    presenter.conversion_banner_changed.connect(banners.append)

    service.status = MotionConversionStatusDTO(is_available=True, microns_per_pulse=21.8)
    bus.publish("motionconversionbecameavailable", MotionConversionBecameAvailable(21.8, "IGUS", "TB6600"))

    assert banners[-1].visible is False


def test_motion_presenter_reads_the_limits_again_when_the_factor_arrives_or_changes():
    """The travel in mm follows µm/increment: the middle of the bench (limits / 2) must follow too."""
    _app()
    bus = InMemoryEventBus()
    service = _MotionService()
    presenter = MotionPresenter(service, bus)
    presenter.initialize()
    limits = []
    presenter.limits_updated.connect(lambda x, y: limits.append((x, y)))

    service.limits = (1200.0, 1160.0)
    bus.publish("motionconversionbecameavailable", MotionConversionBecameAvailable(20.62, "IGUS", "TB6600"))
    service.limits = (1250.0, 1209.0)
    bus.publish("motionconversionchanged", object())

    assert limits == [(1200.0, 1160.0), (1250.0, 1209.0)]


def test_motion_panel_blocks_moves_but_not_stop_while_not_calibrated():
    _app()
    panel = MotionPanelCompact()
    presenter = MotionPresenter(_MotionService(), InMemoryEventBus())
    presenter.conversion_banner_changed.connect(panel.set_calibration_banner)
    presenter.initialize()

    assert not panel.lbl_calibration_banner.isHidden()
    assert not panel.btn_go_both.isEnabled()
    assert not panel.btn_up.isEnabled()
    assert panel.btn_stop.isEnabled() and panel.btn_estop.isEnabled()
    assert panel.btn_home_xy.isEnabled()  # homing works in pulses, the bar calibration needs it

    panel.set_jog_enabled(True)  # a motion event must not unlock a not calibrated bench
    assert not panel.btn_up.isEnabled()


def test_scan_presenter_blocks_start_and_says_why():
    _app()
    bus = InMemoryEventBus()
    presenter = ScanPresenter(_ScanService(), _Export(), bus)
    panel = ScanControlPanel()
    presenter.start_availability_changed.connect(panel.set_start_availability)

    presenter.refresh_start_availability()

    assert not panel.btn_start.isEnabled()
    assert "µm par impulsion" in panel.lbl_start_blocked.text()


def test_scan_start_request_refused_shows_the_typed_reason():
    _app()
    presenter = ScanPresenter(_ScanService(), _Export(), InMemoryEventBus())
    messages = []
    presenter.status_updated.connect(messages.append)

    presenter.on_scan_start_requested({})

    assert "µm par impulsion" in messages[-1]


def test_scan_start_is_enabled_again_on_became_available():
    _app()
    bus = InMemoryEventBus()
    service = _ScanService()
    presenter = ScanPresenter(service, _Export(), bus)
    panel = ScanControlPanel()
    presenter.start_availability_changed.connect(panel.set_start_availability)
    presenter.refresh_start_availability()

    service.refusal = None
    bus.publish("motionconversionbecameavailable", MotionConversionBecameAvailable(21.8, "IGUS", "TB6600"))

    assert panel.btn_start.isEnabled()
    assert panel.lbl_start_blocked.isHidden()


def test_found_missing_event_refreshes_scan_start_availability():
    _app()
    bus = InMemoryEventBus()
    presenter = ScanPresenter(_ScanService(), _Export(), bus)
    seen = []
    presenter.start_availability_changed.connect(seen.append)

    bus.publish("motionconversionfoundmissing", MotionConversionFoundMissing("IGUS", "µm par impulsion", "onglet"))

    assert seen and seen[-1].visible


def test_motion_presenter_relays_the_controller_increments_even_when_not_calibrated():
    from domain.shared_kernel.motion.events.motor_increments_updated.motor_increments_updated import (
        MotorIncrementsUpdated,
    )

    _app()
    bus = InMemoryEventBus()
    presenter = MotionPresenter(_MotionService(), bus)
    received = []
    presenter.increments_updated.connect(lambda x, y: received.append((x, y)))

    bus.publish("motorincrementsupdated", MotorIncrementsUpdated(x_increments=2000, y_increments=-50, is_moving=False))

    assert received == [(2000, -50)]
