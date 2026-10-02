"""MockMotionPort reproduces the bench-measured move duration (port level)."""
import threading
import time

import pytest

from domain.shared_kernel.value_objects.geometric.position_2d import Position2D
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.mocks.adapter_mock_i_motion_port import (
    MEASURED_PORT_TIMING,
    MockMotionPort,
    measured_move_duration_s,
)


def test_duration_is_t0_plus_largest_axis_over_speed():
    t0, speed = MEASURED_PORT_TIMING["slow"]
    duration = measured_move_duration_s(Position2D(600, 600), Position2D(700, 650), "slow")
    assert duration == pytest.approx(t0 + 100 / speed)


def test_diagonal_costs_the_same_as_its_largest_axis():
    start = Position2D(600, 600)
    assert measured_move_duration_s(start, Position2D(650, 650), "medium") == pytest.approx(
        measured_move_duration_s(start, Position2D(650, 600), "medium")
    )


def test_slow_move_from_home_to_bench_center_exceeds_the_30s_scan_timeout():
    # The reason this fidelity matters: ScanApplicationService waits 30 s per move.
    assert measured_move_duration_s(Position2D(0, 0), Position2D(600, 600), "slow") > 30.0


def test_unknown_speed_mode_is_rejected_like_the_real_adapter():
    with pytest.raises(ValueError):
        MockMotionPort().set_speed_mode("turbo")


def test_motion_completed_arrives_after_the_measured_duration():
    bus = InMemoryEventBus()
    port = MockMotionPort(event_bus=bus)
    port.set_speed_mode("fast")
    done = threading.Event()
    bus.subscribe("motioncompleted", lambda e: done.set())

    target = Position2D(10.0, 0.0)
    expected = measured_move_duration_s(Position2D(0, 0), target, "fast")
    start = time.perf_counter()
    port.move_to(target)
    assert done.wait(timeout=5.0)
    assert time.perf_counter() - start == pytest.approx(expected, abs=0.05)
    assert port.get_current_position() == target


def test_explicit_fixed_delay_is_kept_for_fast_logic_tests():
    bus = InMemoryEventBus()
    port = MockMotionPort(event_bus=bus, motion_delay_ms=1)
    done = threading.Event()
    bus.subscribe("motioncompleted", lambda e: done.set())
    start = time.perf_counter()
    port.move_to(Position2D(600.0, 600.0))  # would take ~19 s at medium speed
    assert done.wait(timeout=1.0)
    assert time.perf_counter() - start < 0.5
