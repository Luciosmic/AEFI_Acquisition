import dataclasses

import pytest

from interface.presentation.inertial_sensor_view_model import (
    CHANNELS,
    InertialSensorReadingViewModel,
    build_reading_view_model,
)


def test_channels_have_explicit_labels_in_display_order():
    assert [c.label for c in CHANNELS] == [
        "Accélération (g)",
        "Vitesse angulaire (°/s)",
        "Champ magnétique (µT)",
        "Distance lidar (mm)",
    ]


def test_gyroscope_magnetometer_and_lidar_are_flagged_unverified_with_a_reason():
    flags = {c.key: c.unverified for c in CHANNELS}
    assert flags == {
        "accelerometer": False,
        "gyroscope": True,
        "magnetometer": True,
        "lidar": True,
    }
    for c in CHANNELS:
        assert bool(c.unverified_reason) == c.unverified


def test_lidar_label_says_it_is_provisional():
    lidar = next(c for c in CHANNELS if c.key == "lidar")
    assert "canal provisoire : concept distinct à venir" in lidar.note


def test_build_formats_present_channels_and_dashes_for_absent_ones():
    vm = build_reading_view_model(
        acceleration_g=(0.0, 0.0, 1.0),
        angular_rate_dps=None,
        magnetic_field_ut=(20.0, -5.0, 40.0),
        lidar_distance_mm=1250.0,
        measured_rate_hz=24.96,
        sample_count=42,
    )
    by_key = {c.key: c for c in vm.channels}
    assert by_key["accelerometer"].values == ("+0.0000", "+0.0000", "+1.0000")
    assert by_key["gyroscope"].values == ("—", "—", "—")
    assert by_key["magnetometer"].values == ("+20.00", "-5.00", "+40.00")
    assert by_key["lidar"].values == ("1250",)
    assert vm.measured_rate_hz == 24.96 and vm.sample_count == 42


def test_view_model_is_frozen():
    vm = build_reading_view_model(None, None, None, None, None, 0)
    assert isinstance(vm, InertialSensorReadingViewModel)
    with pytest.raises(dataclasses.FrozenInstanceError):
        vm.sample_count = 1
