"""Caractérisation de acquisition_throughput_characterization : le comportement actuel, sans le changer."""
import dataclasses
import pytest

from domain.test_bench_calibration.value_objects.acquisition_throughput_characterization.acquisition_throughput_characterization import AcquisitionThroughputCharacterization
from domain.test_bench_calibration.value_objects.acquisition_throughput_characterization.acquisition_throughput_characterization import AcquisitionThroughputPoint


def test_acquisitionthroughputpoint_garde_ses_champs() -> None:
    n_avg = 3
    sample_period_s = 1.5
    sample_rate_per_s = 1.5
    adc_conversions_per_s = 1.5
    noise_v_rms = (1.5,)
    noise_rms_v = 1.5
    noise_in_one_second_v = 1.5
    sample_count = 3
    instance = AcquisitionThroughputPoint(n_avg=n_avg, sample_period_s=sample_period_s, sample_rate_per_s=sample_rate_per_s, adc_conversions_per_s=adc_conversions_per_s, noise_v_rms=noise_v_rms, noise_rms_v=noise_rms_v, noise_in_one_second_v=noise_in_one_second_v, sample_count=sample_count)
    assert instance.n_avg == n_avg
    assert instance.sample_period_s == sample_period_s
    assert instance.sample_rate_per_s == sample_rate_per_s
    assert instance.adc_conversions_per_s == adc_conversions_per_s
    assert instance.noise_v_rms == noise_v_rms
    assert instance.noise_rms_v == noise_rms_v
    assert instance.noise_in_one_second_v == noise_in_one_second_v
    assert instance.sample_count == sample_count


def test_acquisitionthroughputpoint_est_immuable() -> None:
    n_avg = 3
    sample_period_s = 1.5
    sample_rate_per_s = 1.5
    adc_conversions_per_s = 1.5
    noise_v_rms = (1.5,)
    noise_rms_v = 1.5
    noise_in_one_second_v = 1.5
    sample_count = 3
    instance = AcquisitionThroughputPoint(n_avg=n_avg, sample_period_s=sample_period_s, sample_rate_per_s=sample_rate_per_s, adc_conversions_per_s=adc_conversions_per_s, noise_v_rms=noise_v_rms, noise_rms_v=noise_rms_v, noise_in_one_second_v=noise_in_one_second_v, sample_count=sample_count)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.n_avg = n_avg  # type: ignore[misc]


def test_acquisitionthroughputcharacterization_garde_ses_champs() -> None:
    points = (AcquisitionThroughputPoint(n_avg=3, sample_period_s=1.5, sample_rate_per_s=1.5, adc_conversions_per_s=1.5, noise_v_rms=(1.5,), noise_rms_v=1.5, noise_in_one_second_v=1.5, sample_count=3),)
    overhead_s = 1.5
    adc_output_rate_hz = None
    fit_max_relative_residual = 1.5
    recommended_n_avg = 3
    noise_relative_uncertainty = 1.5
    instance = AcquisitionThroughputCharacterization(points=points, overhead_s=overhead_s, adc_output_rate_hz=adc_output_rate_hz, fit_max_relative_residual=fit_max_relative_residual, recommended_n_avg=recommended_n_avg, noise_relative_uncertainty=noise_relative_uncertainty)
    assert instance.points == points
    assert instance.overhead_s == overhead_s
    assert instance.adc_output_rate_hz == adc_output_rate_hz
    assert instance.fit_max_relative_residual == fit_max_relative_residual
    assert instance.recommended_n_avg == recommended_n_avg
    assert instance.noise_relative_uncertainty == noise_relative_uncertainty


def test_acquisitionthroughputcharacterization_est_immuable() -> None:
    points = (AcquisitionThroughputPoint(n_avg=3, sample_period_s=1.5, sample_rate_per_s=1.5, adc_conversions_per_s=1.5, noise_v_rms=(1.5,), noise_rms_v=1.5, noise_in_one_second_v=1.5, sample_count=3),)
    overhead_s = 1.5
    adc_output_rate_hz = None
    fit_max_relative_residual = 1.5
    recommended_n_avg = 3
    noise_relative_uncertainty = 1.5
    instance = AcquisitionThroughputCharacterization(points=points, overhead_s=overhead_s, adc_output_rate_hz=adc_output_rate_hz, fit_max_relative_residual=fit_max_relative_residual, recommended_n_avg=recommended_n_avg, noise_relative_uncertainty=noise_relative_uncertainty)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.points = points  # type: ignore[misc]
