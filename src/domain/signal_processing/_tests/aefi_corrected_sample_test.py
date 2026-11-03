from datetime import datetime, timezone
from uuid import uuid4

import pytest

from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement
from domain.signal_processing.aefi_corrected_sample import AefiCorrectedSample
from domain.signal_processing.errors.signal_correction_calibration_missing_error import (
    SignalCorrectionCalibrationMissingError,
)
from domain.signal_processing.events.aefi_sample_corrected.aefi_sample_corrected import AefiSampleCorrected
from domain.signal_processing.value_objects.aefi_signal_correction_calibration.aefi_signal_correction_calibration import (
    AefiSignalCorrectionCalibration,
)

TIMESTAMP = datetime(2026, 10, 9, tzinfo=timezone.utc)


def make_raw(v: float = 1.0) -> AefiVoltageMeasurement:
    return AefiVoltageMeasurement(v, v, v, v, v, v, timestamp=TIMESTAMP)


def test_correct_with_all_stages_disabled_accepts_and_emits_event():
    acquisition_id = uuid4()
    sample = AefiCorrectedSample.correct(
        make_raw(1.0), AefiSignalCorrectionCalibration(), acquisition_id, sample_index=0
    )

    assert sample.measurement.voltage_x_in_phase == pytest.approx(1.0)
    (event,) = sample.domain_events
    assert isinstance(event, AefiSampleCorrected)
    assert event.acquisition_id == acquisition_id
    assert event.sample_index == 0
    assert event.sample == sample.measurement


def test_correct_with_fully_calibrated_stages_accepts_and_emits_event():
    calibration = AefiSignalCorrectionCalibration(
        noise_offset={"x": (0.1, 0.1), "y": (0.1, 0.1), "z": (0.1, 0.1)},
        noise_correction_enabled=True,
        phase_angles={"x": 0.0, "y": 0.0, "z": 0.0},
        phase_correction_enabled=True,
        primary_offset={"x": (0.0, 0.0), "y": (0.0, 0.0), "z": (0.0, 0.0)},
        primary_correction_enabled=True,
    )

    sample = AefiCorrectedSample.correct(make_raw(1.0), calibration, uuid4(), sample_index=1)

    assert sample.measurement is not None
    assert len(sample.domain_events) == 1


def test_domain_events_property_clears_the_list():
    sample = AefiCorrectedSample.correct(
        make_raw(1.0), AefiSignalCorrectionCalibration(), uuid4(), sample_index=0
    )
    assert len(sample.domain_events) == 1
    assert sample.domain_events == []


def test_noise_correction_enabled_without_calibration_for_one_axis_is_rejected():
    calibration = AefiSignalCorrectionCalibration(
        noise_offset={"x": (0.1, 0.1), "y": (0.1, 0.1)},  # missing "z"
        noise_correction_enabled=True,
    )

    with pytest.raises(SignalCorrectionCalibrationMissingError) as excinfo:
        AefiCorrectedSample.correct(make_raw(1.0), calibration, uuid4(), sample_index=0)

    assert excinfo.value.stage == "noise"


def test_phase_correction_enabled_without_calibration_for_one_axis_is_rejected():
    calibration = AefiSignalCorrectionCalibration(
        phase_angles={"x": 0.0, "z": 0.0},  # missing "y"
        phase_correction_enabled=True,
    )

    with pytest.raises(SignalCorrectionCalibrationMissingError) as excinfo:
        AefiCorrectedSample.correct(make_raw(1.0), calibration, uuid4(), sample_index=0)

    assert excinfo.value.stage == "phase"


def test_primary_correction_enabled_without_any_calibration_is_rejected():
    calibration = AefiSignalCorrectionCalibration(primary_correction_enabled=True)

    with pytest.raises(SignalCorrectionCalibrationMissingError) as excinfo:
        AefiCorrectedSample.correct(make_raw(1.0), calibration, uuid4(), sample_index=0)

    assert excinfo.value.stage == "primary"
