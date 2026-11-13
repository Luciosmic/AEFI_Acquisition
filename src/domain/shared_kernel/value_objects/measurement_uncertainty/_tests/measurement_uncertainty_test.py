"""Caractérisation de measurement_uncertainty : le comportement actuel, sans le changer."""
import dataclasses
import pytest

from domain.shared_kernel.value_objects.measurement_uncertainty.measurement_uncertainty import MeasurementUncertainty


def test_measurementuncertainty_garde_ses_champs() -> None:
    max_uncertainty_volts = 1.5
    instance = MeasurementUncertainty(max_uncertainty_volts=max_uncertainty_volts)
    assert instance.max_uncertainty_volts == max_uncertainty_volts


def test_measurementuncertainty_est_immuable() -> None:
    max_uncertainty_volts = 1.5
    instance = MeasurementUncertainty(max_uncertainty_volts=max_uncertainty_volts)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.max_uncertainty_volts = max_uncertainty_volts  # type: ignore[misc]
