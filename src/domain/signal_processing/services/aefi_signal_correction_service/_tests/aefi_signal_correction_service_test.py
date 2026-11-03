import math
from datetime import datetime, timezone

import pytest

from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement
from domain.signal_processing.services.aefi_signal_correction_service.aefi_signal_correction_service import (
    AefiSignalCorrectionService,
)
from domain.signal_processing.value_objects.aefi_signal_correction_calibration.aefi_signal_correction_calibration import (
    AefiSignalCorrectionCalibration,
)

TIMESTAMP = datetime(2026, 10, 9, tzinfo=timezone.utc)


def make_measurement(x_i, x_q, y_i, y_q, z_i, z_q) -> AefiVoltageMeasurement:
    return AefiVoltageMeasurement(
        voltage_x_in_phase=x_i, voltage_x_quadrature=x_q,
        voltage_y_in_phase=y_i, voltage_y_quadrature=y_q,
        voltage_z_in_phase=z_i, voltage_z_quadrature=z_q,
        timestamp=TIMESTAMP,
    )


# --------------------------------------------------------------------------- #
# apply()
# --------------------------------------------------------------------------- #

def test_apply_with_all_corrections_disabled_returns_unchanged_values():
    raw = make_measurement(1.0, 2.0, 3.0, 4.0, 5.0, 6.0)
    calibration = AefiSignalCorrectionCalibration()

    result = AefiSignalCorrectionService.apply(raw, calibration)

    assert result.voltage_x_in_phase == 1.0
    assert result.voltage_x_quadrature == 2.0
    assert result.voltage_y_in_phase == 3.0
    assert result.voltage_y_quadrature == 4.0
    assert result.voltage_z_in_phase == 5.0
    assert result.voltage_z_quadrature == 6.0
    assert result.timestamp == TIMESTAMP


def test_apply_noise_correction_subtracts_offset_per_axis():
    raw = make_measurement(1.0, 2.0, 3.0, 4.0, 5.0, 6.0)
    calibration = AefiSignalCorrectionCalibration(
        noise_offset={"x": (0.1, 0.2), "y": (0.3, 0.4), "z": (0.5, 0.6)},
        noise_correction_enabled=True,
    )

    result = AefiSignalCorrectionService.apply(raw, calibration)

    assert result.voltage_x_in_phase == pytest.approx(0.9)
    assert result.voltage_x_quadrature == pytest.approx(1.8)
    assert result.voltage_y_in_phase == pytest.approx(2.7)
    assert result.voltage_y_quadrature == pytest.approx(3.6)
    assert result.voltage_z_in_phase == pytest.approx(4.5)
    assert result.voltage_z_quadrature == pytest.approx(5.4)


def test_apply_primary_correction_subtracts_offset_per_axis():
    raw = make_measurement(1.0, 2.0, 3.0, 4.0, 5.0, 6.0)
    calibration = AefiSignalCorrectionCalibration(
        primary_offset={"x": (0.1, 0.2), "y": (0.3, 0.4), "z": (0.5, 0.6)},
        primary_correction_enabled=True,
    )

    result = AefiSignalCorrectionService.apply(raw, calibration)

    assert result.voltage_x_in_phase == pytest.approx(0.9)
    assert result.voltage_x_quadrature == pytest.approx(1.8)
    assert result.voltage_z_in_phase == pytest.approx(4.5)
    assert result.voltage_z_quadrature == pytest.approx(5.4)


def test_apply_phase_correction_preserves_sign_by_original_quadrant():
    """Vecteur x d'origine en quadrant II (I<0, Q>0) : theta = atan2(4, -3) (triangle 3-4-5,
    cos=-0.6, sin=0.8). La rotation algebrique donnerait un I positif ; la correction de signe
    (signal_processor.py:79-85) doit le ramener negatif pour preserver le quadrant d'origine."""
    theta_x = math.atan2(4.0, -3.0)
    raw = make_measurement(-3.0, 4.0, 0.0, 0.0, 0.0, 0.0)
    calibration = AefiSignalCorrectionCalibration(
        phase_angles={"x": theta_x, "y": 0.0, "z": 0.0},
        phase_correction_enabled=True,
    )

    result = AefiSignalCorrectionService.apply(raw, calibration)

    assert result.voltage_x_in_phase == pytest.approx(-5.0)
    assert result.voltage_x_quadrature == pytest.approx(0.0, abs=1e-9)


def test_apply_phase_correction_aligns_onto_positive_i_axis_when_sign_matches():
    """Vecteur (0, 5) aligne a theta=pi/2 : la rotation algebrique donne directement un I positif,
    pas de correction de signe necessaire."""
    raw = make_measurement(0.0, 5.0, 0.0, 0.0, 0.0, 0.0)
    calibration = AefiSignalCorrectionCalibration(
        phase_angles={"x": math.pi / 2, "y": 0.0, "z": 0.0},
        phase_correction_enabled=True,
    )

    result = AefiSignalCorrectionService.apply(raw, calibration)

    assert result.voltage_x_in_phase == pytest.approx(5.0)
    assert result.voltage_x_quadrature == pytest.approx(0.0, abs=1e-9)


def test_apply_runs_noise_then_phase_then_primary_in_order():
    """theta=0 (rotation no-op) isole l'ordre bruit -> primaire : 10 - 1 (bruit) = 9,
    puis 9 - 2 (primaire) = 7. Si l'ordre etait inverse, le resultat serait 10 - 2 - 1 = 7
    aussi pour une soustraction simple -- la distinction reelle est que la phase s'applique
    entre les deux, sur la valeur DEJA corrigee du bruit (9), pas sur la valeur brute (10)."""
    raw = make_measurement(10.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    calibration = AefiSignalCorrectionCalibration(
        noise_offset={"x": (1.0, 0.0), "y": (0.0, 0.0), "z": (0.0, 0.0)},
        noise_correction_enabled=True,
        phase_angles={"x": 0.0, "y": 0.0, "z": 0.0},
        phase_correction_enabled=True,
        primary_offset={"x": (2.0, 0.0), "y": (0.0, 0.0), "z": (0.0, 0.0)},
        primary_correction_enabled=True,
    )

    result = AefiSignalCorrectionService.apply(raw, calibration)

    assert result.voltage_x_in_phase == pytest.approx(7.0)


# --------------------------------------------------------------------------- #
# calibrate_noise / calibrate_phase / calibrate_primary
# --------------------------------------------------------------------------- #

def test_calibrate_noise_freezes_current_sample_as_offset_and_enables_stage():
    current = make_measurement(0.01, 0.02, 0.03, 0.04, 0.05, 0.06)
    calibration = AefiSignalCorrectionCalibration()

    updated = AefiSignalCorrectionService.calibrate_noise(current, calibration)

    assert updated.noise_offset == {"x": (0.01, 0.02), "y": (0.03, 0.04), "z": (0.05, 0.06)}
    assert updated.noise_correction_enabled is True
    assert calibration.noise_correction_enabled is False  # original untouched


def test_calibrate_phase_computes_angle_per_axis_and_enables_stage():
    current_pre_phase = make_measurement(0.0, 5.0, 1.0, 0.0, -1.0, 0.0)
    calibration = AefiSignalCorrectionCalibration()

    updated = AefiSignalCorrectionService.calibrate_phase(current_pre_phase, calibration)

    assert updated.phase_angles["x"] == pytest.approx(math.pi / 2)
    assert updated.phase_angles["y"] == pytest.approx(0.0)
    assert updated.phase_angles["z"] == pytest.approx(math.pi)
    assert updated.phase_correction_enabled is True
    assert calibration.phase_correction_enabled is False


def test_calibrate_primary_freezes_current_sample_as_offset_and_enables_stage():
    current_fully_processed = make_measurement(0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
    calibration = AefiSignalCorrectionCalibration()

    updated = AefiSignalCorrectionService.calibrate_primary(current_fully_processed, calibration)

    assert updated.primary_offset == {"x": (0.5, 0.6), "y": (0.7, 0.8), "z": (0.9, 1.0)}
    assert updated.primary_correction_enabled is True
    assert calibration.primary_correction_enabled is False
