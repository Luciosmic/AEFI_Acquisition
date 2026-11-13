"""Caractérisation de sensor_transformation_angles_updated : le comportement actuel, sans le changer."""
import dataclasses
import pytest

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent
from domain.test_bench_calibration.events.sensor_transformation_angles_updated.sensor_transformation_angles_updated import SensorTransformationAnglesUpdated


def test_sensortransformationanglesupdated_garde_ses_champs() -> None:
    theta_x = 1.5
    theta_y = 1.5
    theta_z = 1.5
    instance = SensorTransformationAnglesUpdated(theta_x=theta_x, theta_y=theta_y, theta_z=theta_z)
    assert isinstance(instance, DomainEvent)
    assert instance.theta_x == theta_x
    assert instance.theta_y == theta_y
    assert instance.theta_z == theta_z


def test_sensortransformationanglesupdated_est_immuable() -> None:
    theta_x = 1.5
    theta_y = 1.5
    theta_z = 1.5
    instance = SensorTransformationAnglesUpdated(theta_x=theta_x, theta_y=theta_y, theta_z=theta_z)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.theta_x = theta_x  # type: ignore[misc]
