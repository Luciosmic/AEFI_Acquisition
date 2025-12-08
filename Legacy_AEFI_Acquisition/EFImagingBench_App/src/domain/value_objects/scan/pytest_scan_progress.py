"""Tests for ScanProgress value object."""
import pytest
from .scan_progress import ScanProgress

def test_scan_progress_creation():
    """Test creating valid scan progress."""
    progress = ScanProgress(
        current_point=50,
        total_points=200,
        current_line=5,
        total_lines=20,
        elapsed_time_seconds=10.5,
        estimated_remaining_seconds=31.5
    )
    
    assert progress.current_point == 50
    assert progress.total_points == 200

def test_scan_progress_immutable():
    """Test that progress is immutable."""
    progress = ScanProgress(
        current_point=50,
        total_points=200,
        current_line=5,
        total_lines=20,
        elapsed_time_seconds=10.0,
        estimated_remaining_seconds=30.0
    )
    
    with pytest.raises(AttributeError):
        progress.current_point = 60

def test_scan_progress_percentage_calculation():
    """Test percentage() calculation."""
    progress = ScanProgress(
        current_point=50,
        total_points=200,
        current_line=5,
        total_lines=20,
        elapsed_time_seconds=10.0,
        estimated_remaining_seconds=30.0
    )
    
    assert progress.percentage() == 25.0  # 50/200 * 100

def test_scan_progress_percentage_zero():
    """Test percentage() when no points completed."""
    progress = ScanProgress(
        current_point=0,
        total_points=200,
        current_line=0,
        total_lines=20,
        elapsed_time_seconds=0.0,
        estimated_remaining_seconds=40.0
    )
    
    assert progress.percentage() == 0.0

def test_scan_progress_percentage_complete():
    """Test percentage() when scan is complete."""
    progress = ScanProgress(
        current_point=200,
        total_points=200,
        current_line=20,
        total_lines=20,
        elapsed_time_seconds=40.0,
        estimated_remaining_seconds=0.0
    )
    
    assert progress.percentage() == 100.0

def test_scan_progress_is_complete_true():
    """Test is_complete() returns True when done."""
    progress = ScanProgress(
        current_point=200,
        total_points=200,
        current_line=20,
        total_lines=20,
        elapsed_time_seconds=40.0,
        estimated_remaining_seconds=0.0
    )
    
    assert progress.is_complete()

def test_scan_progress_is_complete_false():
    """Test is_complete() returns False when not done."""
    progress = ScanProgress(
        current_point=50,
        total_points=200,
        current_line=5,
        total_lines=20,
        elapsed_time_seconds=10.0,
        estimated_remaining_seconds=30.0
    )
    
    assert not progress.is_complete()

def test_scan_progress_rejects_negative_current_point():
    """Test that negative current_point is rejected."""
    with pytest.raises(ValueError, match="Invalid current_point"):
        ScanProgress(
            current_point=-1,
            total_points=200,
            current_line=5,
            total_lines=20,
            elapsed_time_seconds=10.0,
            estimated_remaining_seconds=30.0
        )

def test_scan_progress_rejects_current_point_exceeding_total():
    """Test that current_point > total_points is rejected."""
    with pytest.raises(ValueError, match="Invalid current_point"):
        ScanProgress(
            current_point=201,
            total_points=200,
            current_line=5,
            total_lines=20,
            elapsed_time_seconds=10.0,
            estimated_remaining_seconds=30.0
        )

def test_scan_progress_rejects_negative_elapsed_time():
    """Test that negative elapsed time is rejected."""
    with pytest.raises(ValueError, match="elapsed_time_seconds must be >= 0"):
        ScanProgress(
            current_point=50,
            total_points=200,
            current_line=5,
            total_lines=20,
            elapsed_time_seconds=-10.0,
            estimated_remaining_seconds=30.0
        )

def test_scan_progress_rejects_negative_remaining_time():
    """Test that negative remaining time is rejected."""
    with pytest.raises(ValueError, match="estimated_remaining_seconds must be >= 0"):
        ScanProgress(
            current_point=50,
            total_points=200,
            current_line=5,
            total_lines=20,
            elapsed_time_seconds=10.0,
            estimated_remaining_seconds=-5.0
        )

