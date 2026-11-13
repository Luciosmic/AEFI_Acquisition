"""Tests for physical bench limits shared by all scan types."""
from domain.test_bench_configuration.physical_bench_limits import physical_bench_limits as limits
from domain.step_scan.value_objects.scan_zone import scan_zone


def test_limits_are_positive():
    assert limits.PHYSICAL_X_MAX_MM > 0
    assert limits.PHYSICAL_Y_MAX_MM > 0


def test_scan_zone_uses_shared_limits():
    assert scan_zone.PHYSICAL_X_MAX_MM is limits.PHYSICAL_X_MAX_MM
    assert scan_zone.PHYSICAL_Y_MAX_MM is limits.PHYSICAL_Y_MAX_MM


def test_travel_in_increments_is_a_positive_whole_count_per_axis():
    assert isinstance(limits.X_TRAVEL_INCREMENTS, int) and limits.X_TRAVEL_INCREMENTS > 0
    assert isinstance(limits.Y_TRAVEL_INCREMENTS, int) and limits.Y_TRAVEL_INCREMENTS > 0
