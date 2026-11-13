"""MotionControlService.move_relative_increments: the jog in the controller's own unit."""
from unittest.mock import MagicMock

from application.test_bench.motion_control_service.dtos.motion_conversion_status_dto import MotionConversionStatusDTO
from application.test_bench.motion_control_service.motion_control_service import MotionControlService
from application.test_bench.motion_control_service.ports.i_motion_port import IMotionPort
from application.test_bench.raw_increment_motion.ports.i_raw_increment_motion_port import IRawIncrementMotionPort
from domain.test_bench_configuration.physical_bench_limits.physical_bench_limits import X_TRAVEL_INCREMENTS
from infrastructure.in_memory_event_bus.in_memory_event_bus import InMemoryEventBus


def make_service(conversion_available=True, microns_per_pulse=20.62):
    motion_port = MagicMock(spec=IMotionPort)
    motion_port.is_conversion_available.return_value = conversion_available
    motion_port.get_axis_limits.return_value = (1250.0, 1250.0)
    raw_port = MagicMock(spec=IRawIncrementMotionPort)
    conversion = MagicMock()
    conversion.get_status.return_value = MotionConversionStatusDTO(
        is_available=conversion_available, microns_per_pulse=microns_per_pulse if conversion_available else None
    )
    service = MotionControlService(motion_port, InMemoryEventBus(), conversion, raw_increment_port=raw_port)
    return service, raw_port


def _positions(raw, x, y):
    raw.get_position.side_effect = lambda axis: {"X": x, "Y": y}[axis]


def test_a_jog_in_increments_starts_from_where_the_controller_is():
    service, raw = make_service()
    _positions(raw, 500, 700)

    assert service.move_relative_increments(1000, 0).is_success

    assert [c.args for c in raw.move_to.call_args_list] == [("X", 1500)]  # Y not touched


def test_a_jog_in_increments_works_without_the_mm_conversion():
    service, raw = make_service(conversion_available=False)
    _positions(raw, 100, 100)

    assert service.move_relative_increments(0, 250).is_success

    assert [c.args for c in raw.move_to.call_args_list] == [("Y", 350)]


def test_a_jog_in_increments_is_clamped_to_the_travel_like_the_mm_jog():
    service, raw = make_service()
    _positions(raw, 100, X_TRAVEL_INCREMENTS - 10)

    assert service.move_relative_increments(-5000, 0).is_success
    assert service.move_relative_increments(0, 5000).is_success

    moves = [c.args for c in raw.move_to.call_args_list]
    assert moves[0] == ("X", 0)
    assert moves[1][0] == "Y" and moves[1][1] <= 56_346  # never past the end of the Y axis


def test_a_zero_jog_does_nothing():
    service, raw = make_service()

    assert service.move_relative_increments(0, 0).is_success

    raw.move_to.assert_not_called()
