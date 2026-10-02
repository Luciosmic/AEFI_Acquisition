"""Tests for FlyScanLineProjector (positions reported by the controller)."""
from datetime import datetime

import pytest

from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement
from domain.step_scan.services.fly_scan_line_projector.fly_scan_line_projector import FlyScanLineProjector


def m(value):
    return AefiVoltageMeasurement(
        voltage_x_in_phase=value, voltage_x_quadrature=2 * value,
        voltage_y_in_phase=3 * value, voltage_y_quadrature=4 * value,
        voltage_z_in_phase=5 * value, voltage_z_quadrature=6 * value,
        timestamp=datetime(2026, 10, 1),
    )


def x(points):
    return [(k, round(p.voltage_x_in_phase, 6)) for k, p in points]


def projector():
    # 5 points over 40 mm: one every 10 mm.
    return FlyScanLineProjector(n_points=5, line_length_mm=40.0)


def test_a_point_waits_for_the_motor_to_pass_it_and_for_a_later_sample():
    p = projector()
    p.add_sample(0.0, m(0.0))
    assert x(p.add_position(0.0, 0.0)) == [(0, 0.0)]  # point 0: at the start, sample at t=0

    assert p.add_position(1.0, 15.0) == []  # 10 mm crossed at t=2/3, no sample after it yet
    assert x(p.add_sample(1.0, m(3.0))) == [(1, 2.0)]  # sample value at t=2/3


def test_crossing_time_follows_the_reported_positions_not_a_speed_model():
    p = projector()
    p.add_sample(0.0, m(0.0))
    p.add_sample(10.0, m(10.0))  # value = time

    assert x(p.add_position(0.0, 0.0)) == [(0, 0.0)]
    assert p.add_position(2.0, 0.0) == []  # the motor waits 2 s before leaving (latency, ramp)
    points = p.add_position(4.0, 40.0)

    # 10, 20, 30, 40 mm crossed at t = 2.5, 3, 3.5, 4 s.
    assert x(points) == [(1, 2.5), (2, 3.0), (3, 3.5), (4, 4.0)]


def test_every_component_is_interpolated():
    p = projector()
    p.add_position(0.0, 0.0)
    p.add_position(2.0, 20.0)  # 10 mm crossed at t=1
    p.add_sample(0.0, m(0.0))
    (_, point1), _ = p.add_sample(2.0, m(2.0))  # points 1 (t=1) and 2 (t=2)

    assert (
        point1.voltage_x_in_phase, point1.voltage_x_quadrature, point1.voltage_y_in_phase,
        point1.voltage_y_quadrature, point1.voltage_z_in_phase, point1.voltage_z_quadrature,
    ) == pytest.approx((1.0, 2.0, 3.0, 4.0, 5.0, 6.0))


def test_finish_places_the_rest_on_the_trace_or_its_end():
    p = projector()
    p.add_position(0.0, 0.0)
    p.add_position(1.0, 20.0)
    p.add_sample(0.0, m(0.0))
    p.add_sample(0.5, m(5.0))  # last sample: before the 20 mm crossing

    assert x(p.add_sample(0.5, m(5.0))) == []
    # Points 0, 1 were emitted on the first 0.5 s sample; 2 (t=1, no later
    # sample) takes the last one; 3, 4 never reached: last one too.
    assert [k for k, _ in p.finish()] == [2, 3, 4]
    assert p.finish() == []


def test_finish_without_any_sample_has_nothing_to_give():
    p = projector()
    p.add_position(0.0, 0.0)
    with pytest.raises(ValueError):
        p.finish()


def test_a_position_going_backwards_is_ignored():
    p = projector()
    p.add_sample(0.0, m(0.0))
    p.add_sample(10.0, m(10.0))
    p.add_position(0.0, 0.0)
    p.add_position(1.0, 10.0)
    p.add_position(1.5, 5.0)  # jitter

    assert x(p.add_position(3.0, 30.0))[-1] == (3, 3.0)


@pytest.mark.parametrize("n_points, line_length_mm", [(1, 40.0), (5, 0.0)])
def test_rejects_a_line_it_cannot_project(n_points, line_length_mm):
    with pytest.raises(ValueError):
        FlyScanLineProjector(n_points=n_points, line_length_mm=line_length_mm)
