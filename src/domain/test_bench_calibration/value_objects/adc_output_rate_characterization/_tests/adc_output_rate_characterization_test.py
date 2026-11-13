"""Caractérisation de adc_output_rate_characterization : le comportement actuel, sans le changer."""
import dataclasses
import pytest

from domain.test_bench_calibration.value_objects.adc_output_rate_characterization.adc_output_rate_characterization import AdcOutputRateCharacterization
from domain.test_bench_calibration.value_objects.adc_output_rate_characterization.adc_output_rate_characterization import AdcOutputRateMeasurement


def test_adcoutputratemeasurement_garde_ses_champs() -> None:
    oversampling_ratio = 3
    regular_interval_count = 3
    irregular_interval_count = 3
    median_interval_s = 1.5
    mean_interval_s = 1.5
    interval_std_s = 1.5
    output_rate_hz = 1.5
    implied_modulator_frequency_hz = 1.5
    instance = AdcOutputRateMeasurement(oversampling_ratio=oversampling_ratio, regular_interval_count=regular_interval_count, irregular_interval_count=irregular_interval_count, median_interval_s=median_interval_s, mean_interval_s=mean_interval_s, interval_std_s=interval_std_s, output_rate_hz=output_rate_hz, implied_modulator_frequency_hz=implied_modulator_frequency_hz)
    assert instance.oversampling_ratio == oversampling_ratio
    assert instance.regular_interval_count == regular_interval_count
    assert instance.irregular_interval_count == irregular_interval_count
    assert instance.median_interval_s == median_interval_s
    assert instance.mean_interval_s == mean_interval_s
    assert instance.interval_std_s == interval_std_s
    assert instance.output_rate_hz == output_rate_hz
    assert instance.implied_modulator_frequency_hz == implied_modulator_frequency_hz


def test_adcoutputratemeasurement_est_immuable() -> None:
    oversampling_ratio = 3
    regular_interval_count = 3
    irregular_interval_count = 3
    median_interval_s = 1.5
    mean_interval_s = 1.5
    interval_std_s = 1.5
    output_rate_hz = 1.5
    implied_modulator_frequency_hz = 1.5
    instance = AdcOutputRateMeasurement(oversampling_ratio=oversampling_ratio, regular_interval_count=regular_interval_count, irregular_interval_count=irregular_interval_count, median_interval_s=median_interval_s, mean_interval_s=mean_interval_s, interval_std_s=interval_std_s, output_rate_hz=output_rate_hz, implied_modulator_frequency_hz=implied_modulator_frequency_hz)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.oversampling_ratio = oversampling_ratio  # type: ignore[misc]


def test_adcoutputratecharacterization_garde_ses_champs() -> None:
    measurements = (AdcOutputRateMeasurement(oversampling_ratio=3, regular_interval_count=3, irregular_interval_count=3, median_interval_s=1.5, mean_interval_s=1.5, interval_std_s=1.5, output_rate_hz=1.5, implied_modulator_frequency_hz=1.5),)
    mean_modulator_frequency_hz = 1.5
    max_modulator_frequency_relative_deviation = 1.5
    instance = AdcOutputRateCharacterization(measurements=measurements, mean_modulator_frequency_hz=mean_modulator_frequency_hz, max_modulator_frequency_relative_deviation=max_modulator_frequency_relative_deviation)
    assert instance.measurements == measurements
    assert instance.mean_modulator_frequency_hz == mean_modulator_frequency_hz
    assert instance.max_modulator_frequency_relative_deviation == max_modulator_frequency_relative_deviation


def test_adcoutputratecharacterization_est_immuable() -> None:
    measurements = (AdcOutputRateMeasurement(oversampling_ratio=3, regular_interval_count=3, irregular_interval_count=3, median_interval_s=1.5, mean_interval_s=1.5, interval_std_s=1.5, output_rate_hz=1.5, implied_modulator_frequency_hz=1.5),)
    mean_modulator_frequency_hz = 1.5
    max_modulator_frequency_relative_deviation = 1.5
    instance = AdcOutputRateCharacterization(measurements=measurements, mean_modulator_frequency_hz=mean_modulator_frequency_hz, max_modulator_frequency_relative_deviation=max_modulator_frequency_relative_deviation)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.measurements = measurements  # type: ignore[misc]
