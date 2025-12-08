"""Tests for ScanZone value object."""
import pytest
from .scan_zone import ScanZone, PHYSICAL_X_MAX_CM, PHYSICAL_Y_MAX_CM
from ..geometric.position_2d import Position2D

def test_scan_zone_creation():
    """Test creating a valid scan zone."""
    zone = ScanZone(x_min=10.0, x_max=50.0, y_min=20.0, y_max=60.0)
    
    assert zone.x_min == 10.0
    assert zone.x_max == 50.0
    assert zone.y_min == 20.0
    assert zone.y_max == 60.0

def test_scan_zone_immutable():
    """Test that scan zone is immutable."""
    zone = ScanZone(x_min=0.0, x_max=10.0, y_min=0.0, y_max=10.0)
    
    with pytest.raises(AttributeError):
        zone.x_min = 5.0

def test_scan_zone_rejects_x_min_greater_than_max():
    """Test that x_min must be less than x_max."""
    with pytest.raises(ValueError, match="Invalid X range"):
        ScanZone(x_min=50.0, x_max=10.0, y_min=0.0, y_max=10.0)

def test_scan_zone_rejects_y_min_greater_than_max():
    """Test that y_min must be less than y_max."""
    with pytest.raises(ValueError, match="Invalid Y range"):
        ScanZone(x_min=0.0, x_max=10.0, y_min=50.0, y_max=10.0)

def test_scan_zone_rejects_negative_x():
    """Test that negative X values are rejected."""
    with pytest.raises(ValueError, match="Invalid X range"):
        ScanZone(x_min=-10.0, x_max=10.0, y_min=0.0, y_max=10.0)

def test_scan_zone_rejects_negative_y():
    """Test that negative Y values are rejected."""
    with pytest.raises(ValueError, match="Invalid Y range"):
        ScanZone(x_min=0.0, x_max=10.0, y_min=-10.0, y_max=10.0)

def test_scan_zone_rejects_exceeding_physical_x_limit():
    """Test that X values exceeding physical limit are rejected."""
    with pytest.raises(ValueError, match="Invalid X range"):
        ScanZone(x_min=0.0, x_max=PHYSICAL_X_MAX_CM + 1, y_min=0.0, y_max=10.0)

def test_scan_zone_rejects_exceeding_physical_y_limit():
    """Test that Y values exceeding physical limit are rejected."""
    with pytest.raises(ValueError, match="Invalid Y range"):
        ScanZone(x_min=0.0, x_max=10.0, y_min=0.0, y_max=PHYSICAL_Y_MAX_CM + 1)

def test_scan_zone_accepts_maximum_physical_limits():
    """Test that maximum physical limits are accepted."""
    zone = ScanZone(
        x_min=0.0, x_max=PHYSICAL_X_MAX_CM,
        y_min=0.0, y_max=PHYSICAL_Y_MAX_CM
    )
    
    assert zone.x_max == PHYSICAL_X_MAX_CM
    assert zone.y_max == PHYSICAL_Y_MAX_CM

def test_scan_zone_contains_position_inside():
    """Test contains() returns True for position inside zone."""
    zone = ScanZone(x_min=10.0, x_max=50.0, y_min=20.0, y_max=60.0)
    position = Position2D(x=30.0, y=40.0)
    
    assert zone.contains(position)

def test_scan_zone_contains_position_outside():
    """Test contains() returns False for position outside zone."""
    zone = ScanZone(x_min=10.0, x_max=50.0, y_min=20.0, y_max=60.0)
    position = Position2D(x=5.0, y=40.0)
    
    assert not zone.contains(position)

def test_scan_zone_contains_position_on_boundary():
    """Test contains() returns True for position on boundary."""
    zone = ScanZone(x_min=10.0, x_max=50.0, y_min=20.0, y_max=60.0)
    position = Position2D(x=10.0, y=20.0)
    
    assert zone.contains(position)

def test_scan_zone_area_calculation():
    """Test area() calculates correct area."""
    zone = ScanZone(x_min=10.0, x_max=50.0, y_min=20.0, y_max=60.0)
    
    expected_area = (50.0 - 10.0) * (60.0 - 20.0)
    assert zone.area() == expected_area

def test_scan_zone_center_calculation():
    """Test center() calculates correct center position."""
    zone = ScanZone(x_min=10.0, x_max=50.0, y_min=20.0, y_max=60.0)
    
    center = zone.center()
    assert center.x == 30.0
    assert center.y == 40.0

