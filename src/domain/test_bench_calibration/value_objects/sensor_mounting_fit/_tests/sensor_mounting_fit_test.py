"""Caractérisation de sensor_mounting_fit : le comportement actuel, sans le changer."""
import dataclasses
import pytest

from domain.test_bench_calibration.value_objects.sensor_mounting_fit.sensor_mounting_fit import SensorMountingFit
from domain.test_bench_calibration.value_objects.sensor_rotation_angles.sensor_rotation_angles import SensorRotationAngles


def test_sensormountingfit_garde_ses_champs() -> None:
    angles = SensorRotationAngles(theta_x_degrees=1.5, theta_y_degrees=1.5, theta_z_degrees=1.5)
    misalignment_x_degrees = 1.5
    misalignment_y_degrees = 1.5
    response_separation_degrees = 1.5
    instance = SensorMountingFit(angles=angles, misalignment_x_degrees=misalignment_x_degrees, misalignment_y_degrees=misalignment_y_degrees, response_separation_degrees=response_separation_degrees)
    assert instance.angles == angles
    assert instance.misalignment_x_degrees == misalignment_x_degrees
    assert instance.misalignment_y_degrees == misalignment_y_degrees
    assert instance.response_separation_degrees == response_separation_degrees


def test_sensormountingfit_est_immuable() -> None:
    angles = SensorRotationAngles(theta_x_degrees=1.5, theta_y_degrees=1.5, theta_z_degrees=1.5)
    misalignment_x_degrees = 1.5
    misalignment_y_degrees = 1.5
    response_separation_degrees = 1.5
    instance = SensorMountingFit(angles=angles, misalignment_x_degrees=misalignment_x_degrees, misalignment_y_degrees=misalignment_y_degrees, response_separation_degrees=response_separation_degrees)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.angles = angles
