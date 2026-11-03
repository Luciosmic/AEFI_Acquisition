import pytest

from domain.signal_processing.value_objects.aefi_signal_correction_calibration.aefi_signal_correction_calibration import (
    AefiSignalCorrectionCalibration,
)


def test_default_construction_has_no_calibration_and_all_corrections_disabled():
    calibration = AefiSignalCorrectionCalibration()

    assert calibration.noise_offset == {}
    assert calibration.noise_correction_enabled is False
    assert calibration.phase_angles == {}
    assert calibration.phase_correction_enabled is False
    assert calibration.primary_offset == {}
    assert calibration.primary_correction_enabled is False


def test_construction_with_explicit_values():
    calibration = AefiSignalCorrectionCalibration(
        noise_offset={"x": (0.01, 0.02), "y": (0.0, 0.0), "z": (0.0, 0.0)},
        noise_correction_enabled=True,
        phase_angles={"x": 0.1, "y": 0.2, "z": 0.3},
        phase_correction_enabled=True,
        primary_offset={"x": (0.5, 0.5), "y": (0.0, 0.0), "z": (0.0, 0.0)},
        primary_correction_enabled=True,
    )

    assert calibration.noise_offset["x"] == (0.01, 0.02)
    assert calibration.phase_angles["y"] == pytest.approx(0.2)
    assert calibration.primary_offset["z"] == (0.0, 0.0)
    assert calibration.noise_correction_enabled is True
    assert calibration.phase_correction_enabled is True
    assert calibration.primary_correction_enabled is True


def test_is_immutable():
    calibration = AefiSignalCorrectionCalibration()

    with pytest.raises(AttributeError):
        calibration.noise_correction_enabled = True


def test_two_instances_with_same_values_are_equal():
    a = AefiSignalCorrectionCalibration(noise_offset={"x": (1.0, 2.0)})
    b = AefiSignalCorrectionCalibration(noise_offset={"x": (1.0, 2.0)})

    assert a == b
