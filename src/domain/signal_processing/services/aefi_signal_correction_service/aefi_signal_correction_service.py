"""AefiSignalCorrectionService domain service (see aefi_signal_correction_service_intention.md).

Ported identically from interface/presenters/signal_processor.py (SignalPostProcessor),
including the sign-preservation-by-quadrant logic in the phase rotation step.
"""

import math
from dataclasses import replace
from typing import Dict

from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement
from domain.signal_processing.value_objects.aefi_signal_correction_calibration.aefi_signal_correction_calibration import (
    AefiSignalCorrectionCalibration,
)

AXES = ("x", "y", "z")


class AefiSignalCorrectionService:
    """Stateless domain service applying the noise -> phase -> primary correction
    pipeline. Internal to the AefiCorrectedSample aggregate — never called
    directly by the application layer."""

    @staticmethod
    def apply(raw: AefiVoltageMeasurement, calibration: AefiSignalCorrectionCalibration) -> AefiVoltageMeasurement:
        """Apply the enabled correction stages, in order, per axis. Returns a
        NEW AefiVoltageMeasurement; raw is never mutated."""
        updated_fields: Dict[str, float] = {}

        for axis in AXES:
            i_val = getattr(raw, f"voltage_{axis}_in_phase")
            q_val = getattr(raw, f"voltage_{axis}_quadrature")

            # 1. Noise subtraction
            if calibration.noise_correction_enabled:
                offset_i, offset_q = calibration.noise_offset.get(axis, (0.0, 0.0))
                i_val -= offset_i
                q_val -= offset_q

            # 2. Phase rotation (maximize in-phase), with sign preservation by
            # original quadrant (signal_processor.py:62-85).
            if calibration.phase_correction_enabled:
                theta = calibration.phase_angles.get(axis, 0.0)

                if i_val != 0.0:
                    expected_sign = 1.0 if i_val >= 0 else -1.0
                else:
                    expected_sign = 1.0 if q_val >= 0 else -1.0

                cos_t = math.cos(theta)
                sin_t = math.sin(theta)

                i_rotated = i_val * cos_t + q_val * sin_t
                q_new = -i_val * sin_t + q_val * cos_t

                if (i_rotated >= 0) != (expected_sign >= 0):
                    i_val = -i_rotated
                else:
                    i_val = i_rotated
                q_val = q_new

            # 3. Primary field subtraction
            if calibration.primary_correction_enabled:
                offset_i, offset_q = calibration.primary_offset.get(axis, (0.0, 0.0))
                i_val -= offset_i
                q_val -= offset_q

            updated_fields[f"voltage_{axis}_in_phase"] = i_val
            updated_fields[f"voltage_{axis}_quadrature"] = q_val

        return replace(raw, **updated_fields)

    @staticmethod
    def calibrate_noise(
        current: AefiVoltageMeasurement, calibration: AefiSignalCorrectionCalibration
    ) -> AefiSignalCorrectionCalibration:
        """Store current values as noise offset for the 3 axes and enable the stage."""
        noise_offset = dict(calibration.noise_offset)
        for axis in AXES:
            i = getattr(current, f"voltage_{axis}_in_phase")
            q = getattr(current, f"voltage_{axis}_quadrature")
            noise_offset[axis] = (i, q)
        return replace(calibration, noise_offset=noise_offset, noise_correction_enabled=True)

    @staticmethod
    def calibrate_phase(
        current_pre_phase: AefiVoltageMeasurement, calibration: AefiSignalCorrectionCalibration
    ) -> AefiSignalCorrectionCalibration:
        """Calculate the angle to rotate (I, Q) onto the I axis (Q=0), from a sample already
        noise-corrected but NOT yet phase-corrected — the caller is responsible for that
        recomputation (cf. aefi_continuous_reading_presenter.py:133-139)."""
        phase_angles = dict(calibration.phase_angles)
        for axis in AXES:
            i = getattr(current_pre_phase, f"voltage_{axis}_in_phase")
            q = getattr(current_pre_phase, f"voltage_{axis}_quadrature")
            phase_angles[axis] = math.atan2(q, i)
        return replace(calibration, phase_angles=phase_angles, phase_correction_enabled=True)

    @staticmethod
    def calibrate_primary(
        current_fully_processed: AefiVoltageMeasurement, calibration: AefiSignalCorrectionCalibration
    ) -> AefiSignalCorrectionCalibration:
        """Store current values (noise + phase already applied) as primary offset for the
        3 axes and enable the stage."""
        primary_offset = dict(calibration.primary_offset)
        for axis in AXES:
            i = getattr(current_fully_processed, f"voltage_{axis}_in_phase")
            q = getattr(current_fully_processed, f"voltage_{axis}_quadrature")
            primary_offset[axis] = (i, q)
        return replace(calibration, primary_offset=primary_offset, primary_correction_enabled=True)
