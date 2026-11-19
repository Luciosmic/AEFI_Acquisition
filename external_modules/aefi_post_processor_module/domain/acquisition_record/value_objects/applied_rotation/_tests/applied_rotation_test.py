import dataclasses

import pytest

from ..applied_rotation import AppliedRotation


def _rotation(**overrides):
    values = dict(
        angles=(34.9, 45.7, -5.3),
        convention_type="extrinsic",
        convention_order="ZYX",
        convention_direction="sources_to_sensor",
        origin="calibrated",
        calibration_id="cal-2026-11-13",
    )
    values.update(overrides)
    return AppliedRotation(**values)


def test_an_applied_rotation_carries_its_angles_in_degrees_and_its_convention():
    rotation = _rotation()

    assert rotation.angles == (34.9, 45.7, -5.3)
    assert (rotation.convention_type, rotation.convention_order, rotation.convention_direction) == (
        "extrinsic", "ZYX", "sources_to_sensor",
    )
    assert rotation.origin == "calibrated" and rotation.calibration_id == "cal-2026-11-13"


def test_an_applied_rotation_is_immutable():
    with pytest.raises(dataclasses.FrozenInstanceError):
        _rotation().angles = (0.0, 0.0, 0.0)


def test_two_rotations_with_the_same_values_are_equal():
    assert _rotation() == _rotation()
    assert _rotation() != _rotation(angles=(35.3, 45.0, 0.0))


def test_origin_and_calibration_are_optional():
    rotation = _rotation(origin=None, calibration_id=None)

    assert rotation.origin is None and rotation.calibration_id is None


def test_the_angles_are_three_finite_numbers():
    with pytest.raises(ValueError):
        _rotation(angles=(1.0, 2.0))
    with pytest.raises(ValueError):
        _rotation(angles=(1.0, float("nan"), 3.0))
