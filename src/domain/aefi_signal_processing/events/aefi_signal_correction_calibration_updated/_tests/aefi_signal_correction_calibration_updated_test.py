"""Caractérisation de aefi_signal_correction_calibration_updated : le comportement actuel, sans le changer."""
import dataclasses
import pytest

from domain.aefi_signal_processing.events.aefi_signal_correction_calibration_updated.aefi_signal_correction_calibration_updated import AefiSignalCorrectionCalibrationUpdated
from domain.aefi_signal_processing.value_objects.aefi_signal_correction_calibration.aefi_signal_correction_calibration import AefiSignalCorrectionCalibration
from domain.shared_kernel.events.domain_event.domain_event import DomainEvent


def test_aefisignalcorrectioncalibrationupdated_garde_ses_champs() -> None:
    calibration = AefiSignalCorrectionCalibration()
    instance = AefiSignalCorrectionCalibrationUpdated(calibration=calibration)
    assert isinstance(instance, DomainEvent)
    assert instance.calibration == calibration


def test_aefisignalcorrectioncalibrationupdated_est_immuable() -> None:
    calibration = AefiSignalCorrectionCalibration()
    instance = AefiSignalCorrectionCalibrationUpdated(calibration=calibration)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.calibration = calibration  # type: ignore[misc]
