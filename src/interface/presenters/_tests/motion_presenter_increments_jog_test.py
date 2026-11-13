"""MotionPresenter: jog in increments, and the moving state read from the controller's increments."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from types import SimpleNamespace

from PySide6.QtWidgets import QApplication

from domain.shared_kernel.motion.events.motor_increments_updated.motor_increments_updated import MotorIncrementsUpdated
from domain.shared_kernel.operation_result import OperationResult
from infrastructure.in_memory_event_bus.in_memory_event_bus import InMemoryEventBus
from interface.presenters.motion_presenter import MotionPresenter


class _Service:
    def __init__(self):
        self.jogs = []
        self.refusal = None

    def get_axis_limits(self):
        return (1200.0, 1160.0)

    def get_conversion_status(self):
        return SimpleNamespace(is_available=False, motor_name="IGUS", missing_quantity="µm", where_to_enter="Calibration")

    def move_relative_increments(self, dx, dy):
        self.jogs.append((dx, dy))
        return OperationResult.fail(SimpleNamespace(message=self.refusal)) if self.refusal else OperationResult.ok(None)


def _presenter():
    QApplication.instance() or QApplication([])
    service, bus = _Service(), InMemoryEventBus()
    presenter = MotionPresenter(service, bus)
    enabled = []
    presenter.jog_enabled_changed.connect(enabled.append)
    return service, bus, presenter, enabled


def test_a_jog_in_increments_reaches_the_service_and_locks_the_jog_until_the_axes_stop():
    service, bus, presenter, enabled = _presenter()

    presenter.on_jog_increments_requested(250, 0)
    presenter.on_jog_increments_requested(0, 250)  # ignored: still moving

    assert service.jogs == [(250, 0)]
    assert enabled == [False]

    bus.publish("motorincrementsupdated", MotorIncrementsUpdated(x_increments=250, y_increments=0, is_moving=False))
    assert enabled == [False, True]


def test_the_controller_increments_alone_say_when_the_axes_move_even_uncalibrated():
    _service, bus, presenter, enabled = _presenter()
    states = []
    presenter.status_updated.connect(states.append)

    bus.publish("motorincrementsupdated", MotorIncrementsUpdated(x_increments=10, y_increments=0, is_moving=True))
    bus.publish("motorincrementsupdated", MotorIncrementsUpdated(x_increments=20, y_increments=0, is_moving=False))

    assert states == [True, False]
    assert enabled == [False, True]


def test_a_refused_jog_in_increments_unlocks_and_says_why():
    service, _bus, presenter, enabled = _presenter()
    service.refusal = "course dépassée"
    errors = []
    presenter.operation_failed.connect(errors.append)

    presenter.on_jog_increments_requested(1, 0)

    assert errors == ["course dépassée"]
    assert enabled == [False, True]
