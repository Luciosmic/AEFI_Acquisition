"""
Bar Profile Analysis

See bar_profile_analysis_intention.md.
"""

import bisect
from typing import List, Sequence, Tuple

import numpy as np

from domain.calibration.errors.bar_profile_unusable_error import BarProfileUnusableError
from domain.calibration.value_objects.bar_coarse_localization.bar_coarse_localization import (
    BarCoarseLocalization,
)

# (reception time s, value): a motor position in increments, or a LIDAR distance in mm.
TimedValue = Tuple[float, float]
# (motor increment, LIDAR distance mm)
ProfilePoint = Tuple[float, float]

MIN_PROFILE_POINTS = 10
# Share of "on bar" points tolerated outside the bar run (noise flips).
MAX_STRAY_ON_BAR_SHARE = 0.05
_MAD_TO_SIGMA = 1.4826


def pair_by_reception_time(
    positions: Sequence[TimedValue], samples: Sequence[TimedValue]
) -> List[ProfilePoint]:
    """Each LIDAR sample paired with the motor position interpolated at its
    reception time. Samples outside the time span of the positions are dropped."""
    ordered = sorted(positions)
    times = [t for t, _ in ordered]
    profile: List[ProfilePoint] = []
    if len(ordered) < 2:
        return profile
    for t, distance in samples:
        if t < times[0] or t > times[-1]:
            continue
        i = bisect.bisect_right(times, t)
        if i >= len(times):
            profile.append((ordered[-1][1], distance))
            continue
        (t0, n0), (t1, n1) = ordered[i - 1], ordered[i]
        n = n0 if t1 == t0 else n0 + (n1 - n0) * (t - t0) / (t1 - t0)
        profile.append((n, distance))
    return profile


def locate_bar(profile: Sequence[ProfilePoint], min_contrast_mm: float = 10.0) -> BarCoarseLocalization:
    """Plateaus, threshold and coarse fronts of the single bar in a fly scan profile."""
    if len(profile) < MIN_PROFILE_POINTS:
        raise BarProfileUnusableError(
            f"profil trop court : {len(profile)} point(s) LIDAR apparié(s) pendant le fly scan "
            f"(au moins {MIN_PROFILE_POINTS})"
        )
    points = sorted(profile)
    increments = np.array([n for n, _ in points], dtype=float)
    distances = np.array([d for _, d in points], dtype=float)

    low, high = np.percentile(distances, [5, 95])
    if high - low < min_contrast_mm:
        raise BarProfileUnusableError(
            f"pas de créneau : contraste {high - low:.1f} mm < {min_contrast_mm:.1f} mm "
            "(barre absente ou hors de la trajectoire du LIDAR ?)"
        )
    provisional = (low + high) / 2.0
    on_bar_distance = float(np.median(distances[distances < provisional]))
    off_bar_distance = float(np.median(distances[distances >= provisional]))
    threshold = (on_bar_distance + off_bar_distance) / 2.0
    on_bar = distances < threshold

    start, end = _longest_true_run(on_bar)
    if start == 0:
        raise BarProfileUnusableError(
            "la barre commence dès le début de la course : pas de plateau hors barre côté origine"
        )
    if end == len(on_bar) - 1:
        raise BarProfileUnusableError(
            "la barre va jusqu'à la butée opposée : pas de plateau hors barre côté fin de course"
        )
    stray = int(on_bar.sum()) - (end - start + 1)
    off_count = len(on_bar) - (end - start + 1)
    if stray > MAX_STRAY_ON_BAR_SHARE * off_count:
        raise BarProfileUnusableError(
            f"plusieurs zones courtes : {stray} point(s) « sur la barre » en dehors de la barre "
            "(un seul objet doit passer sous le LIDAR)"
        )

    plateau_noise = max(_robust_sigma(distances[on_bar]), _robust_sigma(distances[~on_bar]))
    return BarCoarseLocalization(
        on_bar_distance_mm=on_bar_distance,
        off_bar_distance_mm=off_bar_distance,
        plateau_noise_mm=plateau_noise,
        first_front_increment=float((increments[start - 1] + increments[start]) / 2.0),
        second_front_increment=float((increments[end] + increments[end + 1]) / 2.0),
        profile_point_count=len(points),
    )


def _longest_true_run(flags: np.ndarray) -> Tuple[int, int]:
    """(first, last) index of the longest run of True; raises if there is none."""
    best = (-1, -2)
    run_start = None
    for i, flag in enumerate(flags):
        if flag and run_start is None:
            run_start = i
        if run_start is not None and (not flag or i == len(flags) - 1):
            run_end = i if flag else i - 1
            if run_end - run_start > best[1] - best[0]:
                best = (run_start, run_end)
            run_start = None
    if best[0] < 0:
        raise BarProfileUnusableError("aucun point sur la barre dans le profil")
    return best


def _robust_sigma(values: np.ndarray) -> float:
    if len(values) == 0:
        return 0.0
    return float(_MAD_TO_SIGMA * np.median(np.abs(values - np.median(values))))
