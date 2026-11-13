"""Caractérisation de errors : le comportement actuel, sans le changer."""
import pytest

from domain.aefi_signal_processing.errors.signal_correction_calibration_missing_error import SignalCorrectionCalibrationMissingError


def test_signalcorrectioncalibrationmissingerror_nomme_ses_arguments_dans_son_message() -> None:
    with pytest.raises(SignalCorrectionCalibrationMissingError) as info:
        raise SignalCorrectionCalibrationMissingError('valeur_stage', 'valeur_calibration')  # type: ignore[arg-type]
    assert info.value.stage == 'valeur_stage'
    assert info.value.calibration == 'valeur_calibration'
    assert "valeur_stage" in str(info.value)
