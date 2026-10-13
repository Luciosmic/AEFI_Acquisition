"""
Bench without mm/pulse conversion: MotionControlService refuses with a typed
error, MotionConversionHandler says what is missing and applies the
conversion live once the missing quantity is entered (service chain on
in-memory repositories, motion port reduced to its conversion state).
"""
from typing import List, Optional
from unittest.mock import MagicMock

import pytest

from application.services.hardware_component_service.hardware_component_service import HardwareComponentService
from application.services.mechanical_transmission_calibration_service.mechanical_transmission_calibration_service import (
    MechanicalTransmissionCalibrationService,
)
from application.services.motion_control_service.errors.motion_control_error import (
    MotionConversionUnavailable,
)
from application.services.motion_control_service.motion_control_service import MotionControlService
from application.services.motion_control_service.motion_conversion_handler import MotionConversionHandler
from application.services.motion_control_service.ports.i_motion_port import IMotionPort
from application.services.motion_control_service.ports.motion_conversion_unavailable_error import (
    MotionConversionUnavailableError,
)
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.persistence.calibration.fake.fake_hardware_component_repository import (
    FakeHardwareComponentRepository,
)
from infrastructure.persistence.calibration.fake.fake_mechanical_transmission_calibration_repository import (
    FakeMechanicalTransmissionCalibrationRepository,
)

BENCH_SETTING = dict(microsteps=16, driver_current_a=3.5, driver_peak_current_a=4.0, travel_per_motor_revolution_mm=69.76)


class MotionPortConversionState:
    """MagicMock port whose conversion state follows set_microns_per_pulse()."""

    def __init__(self) -> None:
        self.port = MagicMock(spec=IMotionPort)
        self.microns_per_pulse: Optional[float] = None
        self.port.is_conversion_available.side_effect = lambda: self.microns_per_pulse is not None
        self.port.set_microns_per_pulse.side_effect = self._set
        self.port.get_current_position.return_value = Position2D(0.0, 0.0)
        self.port.get_axis_limits.return_value = (200.0, 200.0)

        def refuse(*_args, **_kwargs):
            if self.microns_per_pulse is None:
                raise MotionConversionUnavailableError("move_to")

        self.port.move_to.side_effect = refuse

    def _set(self, value: float) -> None:
        self.microns_per_pulse = value


@pytest.fixture
def bus():
    return InMemoryEventBus()


@pytest.fixture
def components(bus):
    return HardwareComponentService(FakeHardwareComponentRepository(), bus)


@pytest.fixture
def stack(bus, components):
    """Historical motor file: IGUS motor characterized without full_steps_per_revolution."""
    components.record_characterization("motors", "IGUS-S-AN-060-035-060", {"rated_current_a": 4.2})
    components.mount_component("motors", "IGUS-S-AN-060-035-060")
    components.record_characterization("stepper_driver", "TB6600", {"max_current_a": 3.5})
    components.mount_component("stepper_driver", "TB6600")
    transmission = MechanicalTransmissionCalibrationService(
        FakeMechanicalTransmissionCalibrationRepository(), components._repository, bus
    )
    transmission.record_calibration(**BENCH_SETTING)
    state = MotionPortConversionState()
    handler = MotionConversionHandler(state.port, transmission, bus)
    service = MotionControlService(state.port, bus, conversion_status=handler)
    received: List[object] = []
    bus.subscribe("motionconversionfoundmissing", received.append)
    bus.subscribe("motionconversionbecameavailable", received.append)
    return state, handler, service, received


def test_startup_without_steps_per_revolution_does_not_raise_and_says_what_is_missing(stack):
    state, handler, _service, received = stack

    status = handler.apply_current_transmission()

    assert not status.is_available
    assert status.motor_name == "IGUS-S-AN-060-035-060"
    assert status.missing_quantity == "Pas par tour"
    assert "Moteurs" in status.where_to_enter
    assert [type(e).__name__ for e in received] == ["MotionConversionFoundMissing"]
    assert state.microns_per_pulse is None  # never a default value


def test_move_is_refused_with_a_typed_error_before_reaching_the_port(stack):
    state, handler, service, _received = stack
    handler.apply_current_transmission()

    result = service.move_absolute(10.0, 10.0)

    assert result.is_failure
    assert isinstance(result.error, MotionConversionUnavailable)
    assert result.error.missing_quantity == "Pas par tour"
    assert "Pas par tour" in result.error.message
    state.port.move_to.assert_not_called()


@pytest.mark.parametrize(
    "command",
    [
        lambda s: s.move_relative(1.0, 1.0),
        lambda s: s.move_absolute_x(1.0),
        lambda s: s.move_absolute_y(1.0),
        lambda s: s.home_x(),
        lambda s: s.home_y(),
        lambda s: s.home_xy(),
    ],
)
def test_every_move_and_home_is_refused_when_not_calibrated(stack, command):
    _state, handler, service, _received = stack
    handler.apply_current_transmission()

    result = command(service)

    assert isinstance(result.error, MotionConversionUnavailable)


def test_stop_and_emergency_stop_stay_available(stack):
    _state, handler, service, _received = stack
    handler.apply_current_transmission()

    assert service.stop().is_success
    assert service.emergency_stop().is_success


def test_port_refusal_is_translated_even_without_the_service_guard(bus):
    state = MotionPortConversionState()
    service = MotionControlService(state.port, bus)
    state.port.is_conversion_available.side_effect = None
    state.port.is_conversion_available.return_value = True  # guard passes, port still refuses

    result = service.move_absolute(1.0, 1.0)

    assert isinstance(result.error, MotionConversionUnavailable)


def test_entering_steps_per_revolution_applies_the_conversion_without_restart(stack, components):
    state, handler, service, received = stack
    handler.apply_current_transmission()

    components.record_characterization(
        "motors", "IGUS-S-AN-060-035-060", {"full_steps_per_revolution": 200, "rated_current_a": 4.2}
    )

    assert state.microns_per_pulse == pytest.approx(21.8)
    assert handler.get_status().is_available
    assert [type(e).__name__ for e in received] == ["MotionConversionFoundMissing", "MotionConversionBecameAvailable"]
    assert service.get_conversion_status().is_available
    assert service.move_absolute(10.0, 10.0).is_success


def test_already_applied_conversion_is_not_changed_by_a_later_event(stack, components):
    state, handler, _service, received = stack
    components.record_characterization(
        "motors", "IGUS-S-AN-060-035-060", {"full_steps_per_revolution": 200, "rated_current_a": 4.2}
    )
    handler.apply_current_transmission()
    applied = state.microns_per_pulse
    received.clear()

    components.record_characterization(
        "motors", "IGUS-S-AN-060-035-060", {"full_steps_per_revolution": 400, "rated_current_a": 4.2}
    )

    assert state.microns_per_pulse == applied
    assert received == []


def test_unchanged_gap_is_not_republished(stack, components):
    _state, handler, _service, received = stack
    handler.apply_current_transmission()

    components.record_characterization("motors", "IGUS-S-AN-060-035-060", {"rated_current_a": 4.0})

    assert [type(e).__name__ for e in received] == ["MotionConversionFoundMissing"]
