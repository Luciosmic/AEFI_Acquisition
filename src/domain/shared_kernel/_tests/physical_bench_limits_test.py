"""Tests for physical bench limits shared by all scan types."""
from domain.shared_kernel import physical_bench_limits as limits
from domain.step_scan.value_objects.scan_zone import scan_zone


def test_limits_are_positive():
    assert limits.PHYSICAL_X_MAX_MM > 0
    assert limits.PHYSICAL_Y_MAX_MM > 0
    assert limits.PHYSICAL_Z_MAX_MM > 0


def test_scan_zone_uses_shared_limits():
    assert scan_zone.PHYSICAL_X_MAX_MM is limits.PHYSICAL_X_MAX_MM
    assert scan_zone.PHYSICAL_Y_MAX_MM is limits.PHYSICAL_Y_MAX_MM
