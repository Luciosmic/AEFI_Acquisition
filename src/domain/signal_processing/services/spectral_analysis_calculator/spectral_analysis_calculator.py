"""SpectralAnalysisCalculator domain service (see spectral_analysis_calculator_intention.md)."""

from datetime import datetime
from typing import Dict, Sequence, Tuple

import numpy as np

from domain.signal_processing.value_objects.spectral_analysis_result.spectral_analysis_result import (
    SpectralAnalysisResult,
)


class SpectralAnalysisCalculator:
    """Stateless domain service: resamples a (possibly irregularly-sampled) window
    of multi-channel samples onto a uniform time grid, applies a Hann window, and
    computes the real FFT amplitude spectrum per channel. Pure, deterministic, no I/O."""

    @staticmethod
    def compute(
        samples: Sequence[Tuple[datetime, Dict[str, float]]],
        window_duration_s: float,
    ) -> SpectralAnalysisResult:
        if len(samples) < 2:
            raise ValueError("SpectralAnalysisCalculator.compute requires at least 2 samples")

        window_start = samples[0][0]
        window_end = samples[-1][0]

        # 1. Relative seconds since the first sample.
        t_arr = np.array([(t - window_start).total_seconds() for t, _ in samples], dtype=float)
        dt_mean = float(np.mean(np.diff(t_arr)))
        if dt_mean <= 0:
            raise ValueError("samples must be strictly increasing in time")

        # 2. Uniform grid over the actual span of the window.
        n_points = max(2, round(window_duration_s / dt_mean))
        t_uniform = np.linspace(t_arr[0], t_arr[-1], n_points)
        uniform_step = (t_uniform[-1] - t_uniform[0]) / (n_points - 1)

        # 4. Hann window (computed once, reused for every channel).
        window = np.hanning(n_points)
        window_sum = float(np.sum(window))

        channel_names = list(samples[0][1].keys())
        amplitudes_by_channel: Dict[str, Tuple[float, ...]] = {}
        frequencies_hz: Tuple[float, ...] = ()

        for channel in channel_names:
            y_arr = np.array([values[channel] for _, values in samples], dtype=float)

            # 3. Linear interpolation onto the uniform grid.
            y_uniform = np.interp(t_uniform, t_arr, y_arr)

            y_windowed = y_uniform * window

            # 5. Real FFT.
            spectrum = np.fft.rfft(y_windowed)
            freqs = np.fft.rfftfreq(n_points, d=uniform_step)

            # 6. Amplitude normalization.
            amplitude = np.abs(spectrum) * 2.0 / window_sum

            frequencies_hz = tuple(freqs.tolist())
            amplitudes_by_channel[channel] = tuple(amplitude.tolist())

        return SpectralAnalysisResult(
            frequencies_hz=frequencies_hz,
            amplitudes_by_channel=amplitudes_by_channel,
            window_start=window_start,
            window_end=window_end,
            sample_count=len(samples),
        )
