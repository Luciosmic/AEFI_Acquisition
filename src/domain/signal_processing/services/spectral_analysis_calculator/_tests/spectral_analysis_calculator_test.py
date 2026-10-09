"""Tests for SpectralAnalysisCalculator.

Reuses the sinusoid + jitter synthetic pattern already validated in
src/infrastructure/hardware/micro_controller/ads131a04/_tests/bruit_adc_50hz_secteur_characterization_test.py
to check that a known injected frequency survives the resampling pipeline.
"""
from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from domain.signal_processing.services.spectral_analysis_calculator.spectral_analysis_calculator import (
    SpectralAnalysisCalculator,
)

T0 = datetime(2026, 10, 9, tzinfo=timezone.utc)


def make_synthetic_samples(frequency_hz: float, fs_hz: float, duration_s: float, jitter_s: float = 0.0005, seed: int = 42):
    """Sinusoid at `frequency_hz`, nominally sampled at `fs_hz`, with uniform random
    jitter on each sample's timestamp (cf. ADR-003: the FTDI/MCU round-trip, not the
    ADC, is the source of timing jitter)."""
    rng = np.random.default_rng(seed)
    nominal_dt = 1.0 / fs_hz
    n = int(duration_s * fs_hz)
    samples = []
    for i in range(n):
        t_nominal = i * nominal_dt
        t_actual = t_nominal + rng.uniform(-jitter_s, jitter_s)
        value = np.sin(2 * np.pi * frequency_hz * t_actual)
        samples.append((T0 + timedelta(seconds=t_actual), {"Ux In-Phase": float(value)}))
    samples.sort(key=lambda s: s[0])
    return samples


def test_compute_finds_peak_at_injected_frequency():
    samples = make_synthetic_samples(frequency_hz=10.0, fs_hz=150.0, duration_s=2.0)

    result = SpectralAnalysisCalculator.compute(samples, window_duration_s=2.0)

    freqs = np.array(result.frequencies_hz)
    amplitudes = np.array(result.amplitudes_by_channel["Ux In-Phase"])
    peak_freq = freqs[np.argmax(amplitudes)]

    assert peak_freq == pytest.approx(10.0, abs=0.5)


def test_result_carries_window_metadata():
    samples = make_synthetic_samples(frequency_hz=10.0, fs_hz=150.0, duration_s=1.0)

    result = SpectralAnalysisCalculator.compute(samples, window_duration_s=1.0)

    assert result.sample_count == len(samples)
    assert result.window_start == samples[0][0]
    assert result.window_end == samples[-1][0]


def test_computes_all_channels_present_in_samples():
    samples = [
        (T0 + timedelta(seconds=i * 0.01), {"Ux In-Phase": float(i), "Uy In-Phase": float(-i)})
        for i in range(50)
    ]

    result = SpectralAnalysisCalculator.compute(samples, window_duration_s=0.5)

    assert set(result.amplitudes_by_channel.keys()) == {"Ux In-Phase", "Uy In-Phase"}
    assert len(result.amplitudes_by_channel["Ux In-Phase"]) == len(result.frequencies_hz)


def test_rejects_fewer_than_two_samples():
    with pytest.raises(ValueError):
        SpectralAnalysisCalculator.compute([(T0, {"Ux In-Phase": 0.0})], window_duration_s=1.0)
