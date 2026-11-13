"""MotionControlService.move_to_increments: setpoints in the controller's own unit."""
from unittest.mock import MagicMock

import pytest

from application.test_bench.motion_control_service.dtos.motion_conversion_status_dto import MotionConversionStatusDTO
from application.test_bench.motion_control_service.errors.motion_control_error import MotionCommandFailed
from application.test_bench.motion_control_service.motion_control_service import MotionControlService
from application.test_bench.motion_control_service.ports.i_motion_port import IMotionPort
from application.test_bench.raw_increment_motion.ports.i_raw_increment_motion_port import IRawIncrementMotionPort
from application.test_bench.raw_increment_motion.ports.raw_increment_motion_error import RawIncrementMotionError
from infrastructure.in_memory_event_bus.in_memory_event_bus import InMemoryEventBus


def make_service(conversion_available=True, microns_per_pulse=21.46):
    motion_port = MagicMock(spec=IMotionPort)
    motion_port.is_conversion_available.return_value = conversion_available
    motion_port.get_axis_limits.return_value = (1270.0, 1270.0)
    raw_port = MagicMock(spec=IRawIncrementMotionPort)
    conversion = MagicMock()
    conversion.get_status.return_value = MotionConversionStatusDTO(
        is_available=conversion_available, microns_per_pulse=microns_per_pulse if conversion_available else None
    )
    service = MotionControlService(motion_port, InMemoryEventBus(), conversion, raw_increment_port=raw_port)
    return service, raw_port


def test_both_axes_move_to_their_increments():
    service, raw = make_service()

    assert service.move_to_increments(6290, 100).is_success

    assert [c.args for c in raw.move_to.call_args_list] == [("X", 6290), ("Y", 100)]


def test_one_axis_leaves_the_other_alone():
    service, raw = make_service()

    assert service.move_to_increments(None, 500).is_success

    assert [c.args for c in raw.move_to.call_args_list] == [("Y", 500)]


def test_works_without_any_mm_conversion():
    service, raw = make_service(conversion_available=False)

    assert service.move_to_increments(6290, None).is_success

    raw.move_to.assert_called_once_with("X", 6290)


def test_negative_setpoint_is_refused_before_anything_moves():
    service, raw = make_service()

    result = service.move_to_increments(100, -1)

    assert isinstance(result.error, MotionCommandFailed) and "négatif" in result.error.message
    raw.move_to.assert_not_called()


def test_setpoint_beyond_the_travel_is_refused_when_the_conversion_is_known():
    service, raw = make_service()  # 1270 mm / 21.46 µm = 59179.87 increments: 59179 is the last one inside the travel

    result = service.move_to_increments(59_180, None)

    assert "au-delà de la course" in result.error.message
    raw.move_to.assert_not_called()
    assert service.move_to_increments(59_179, None).is_success


def test_controller_failure_is_translated():
    service, raw = make_service()
    raw.move_to.side_effect = RawIncrementMotionError("déplacement sur l'axe X : non référencé")

    result = service.move_to_increments(10, None)

    assert isinstance(result.error, MotionCommandFailed) and "non référencé" in result.error.message


def test_no_raw_port_is_a_clear_failure():
    service = MotionControlService(MagicMock(spec=IMotionPort), InMemoryEventBus())

    assert "pilote en incréments" in service.move_to_increments(1, 1).error.message


def test_the_last_increment_of_the_travel_is_accepted_whatever_the_float_rounding():
    from domain.test_bench_configuration.physical_bench_limits.physical_bench_limits import Y_TRAVEL_INCREMENTS

    service, raw = make_service(microns_per_pulse=20.62)
    service._motion_port.get_axis_limits.return_value = (1200.0, Y_TRAVEL_INCREMENTS * (20.62 / 1000.0))

    assert service.move_to_increments(None, Y_TRAVEL_INCREMENTS).is_success
    assert not service.move_to_increments(None, Y_TRAVEL_INCREMENTS + 1).is_success
