"""
Column Stabilization (see column_stabilization_intention.md)

Waits, after a move, until the column is back at rest according to the
accelerometer of the inertial probe — and falls back to the fixed
stabilization delay whenever the accelerometer cannot tell.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Callable, Optional, Tuple

from domain.scan.events.column_settled.column_settled import (
    SETTLE_INTERRUPTED,
    SETTLED_ON_ACCELEROMETER,
    SETTLED_ON_FIXED_DELAY,
    SETTLED_ON_TIMEOUT,
)
from domain.scan.value_objects.column_rest_criterion.column_rest_criterion import ColumnRestCriterion
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus

logger = logging.getLogger(__name__)

# Topic of InertialProbeSampleAcquired, published by the inertial probe acquisition worker.
INERTIAL_PROBE_SAMPLE_TOPIC = "inertialprobesampleacquired"

# How the wait after a move ended (names owned by the ColumnSettled event).
ACCELEROMETER = SETTLED_ON_ACCELEROMETER
FIXED_DELAY = SETTLED_ON_FIXED_DELAY
TIMEOUT = SETTLED_ON_TIMEOUT
INTERRUPTED = SETTLE_INTERRUPTED


@dataclass(frozen=True)
class RestMeasurement:
    """Rest level of the still column ([g]); None with the reason when it could not be measured."""

    vibration_g: Optional[float]
    sample_count: int = 0
    unavailable_reason: Optional[str] = None


@dataclass(frozen=True)
class StabilizationOutcome:
    """How one wait ended. Units: s and [g]; vibration/threshold None when not judged."""

    method: str
    waited_s: float
    vibration_g: Optional[float] = None
    threshold_g: Optional[float] = None


class ColumnStabilization:
    """Buffers the accelerometer samples published on the event bus and judges the column's rest.

    Time base: the samples' `timestamp_s` (perf_counter at reception on the PC) and
    the injected `clock` must be the same monotonic clock.
    """

    # Samples kept in memory: the longest window ever read is the rest measurement.
    KEEP_S = 60.0
    # Delay between two judgements of the window while the column vibrates,
    # and bound on the reaction to a cancel during a wait.
    POLL_S = 0.1
    # No sample for this long: the accelerometer is not streaming (25 Hz nominal).
    SILENCE_S = 1.0

    def __init__(
        self,
        event_bus: IDomainEventBus,
        criterion: ColumnRestCriterion = ColumnRestCriterion(),
        clock: Callable[[], float] = time.perf_counter,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._event_bus = event_bus
        self.criterion = criterion
        self._clock = clock
        self._sleep = sleep
        self._samples: deque = deque()  # (timestamp_s, (ax, ay, az))
        self._lock = threading.Lock()
        event_bus.subscribe(INERTIAL_PROBE_SAMPLE_TOPIC, self._on_sample)

    def close(self) -> None:
        self._event_bus.unsubscribe(INERTIAL_PROBE_SAMPLE_TOPIC, self._on_sample)

    # --- samples -------------------------------------------------------------------------

    def _on_sample(self, event) -> None:
        acceleration = getattr(event, "acceleration_g", None)
        if acceleration is None:  # accelerometer channel not streamed
            return
        with self._lock:
            self._samples.append((event.timestamp_s, tuple(acceleration)))
            while self._samples and self._samples[0][0] < event.timestamp_s - self.KEEP_S:
                self._samples.popleft()

    def _vibration(self, t_a: float, t_b: float) -> Tuple[Optional[float], int]:
        with self._lock:
            window = [a for t, a in self._samples if t_a <= t <= t_b]
        return ColumnRestCriterion.vibration_g(window), len(window)

    def _is_streaming(self, now: float) -> bool:
        with self._lock:
            return bool(self._samples) and self._samples[-1][0] >= now - self.SILENCE_S

    def _wait_until(self, end: float, should_stop: Callable[[], bool]) -> bool:
        """Sleep until `end` in POLL_S steps. False if the scan stopped meanwhile."""
        while True:
            if should_stop():
                return False
            remaining = end - self._clock()
            if remaining <= 0:
                return True
            self._sleep(min(self.POLL_S, remaining))

    # --- rest level ----------------------------------------------------------------------

    def measure_rest(self, scan_id, should_stop: Callable[[], bool]) -> RestMeasurement:
        """Vibration of the still column over `rest_measurement_s`, before the first move.

        None — the scan then waits the fixed delay at every point — when the
        accelerometer is not streaming, falls silent, or the scan stops meanwhile.
        """
        start = self._clock()
        if not self._is_streaming(start):
            logger.info("ColumnStabilization: scan_id=%s accelerometer not streaming: fixed stabilization delay "
                        "for this scan (start the inertial probe acquisition to settle on the accelerometer)", scan_id)
            return RestMeasurement(None, 0, "accéléromètre non en acquisition au démarrage du scan")
        logger.info("ColumnStabilization: scan_id=%s measuring the column rest level for %.0f s — do not touch "
                    "the bench", scan_id, self.criterion.rest_measurement_s)
        end = start + self.criterion.rest_measurement_s
        if not self._wait_until(end, should_stop):
            logger.info("ColumnStabilization: scan_id=%s scan stopped during the rest measurement", scan_id)
            return RestMeasurement(None, 0, "scan arrêté pendant la mesure du repos")
        rest_g, n = self._vibration(start, end)
        # Still streaming at the end: a sensor that died mid-measurement gives no rest level.
        if rest_g is None or not self._is_streaming(self._clock()):
            logger.warning("ColumnStabilization: scan_id=%s accelerometer silent during the rest measurement "
                           "(n=%d): fixed stabilization delay for this scan", scan_id, n)
            return RestMeasurement(None, n, "accéléromètre muet pendant la mesure du repos")
        logger.info("ColumnStabilization: scan_id=%s rest level rest_mg=%.2f threshold_mg=%.2f n=%d",
                    scan_id, rest_g * 1000, self.criterion.threshold_g(rest_g) * 1000, n)
        return RestMeasurement(rest_g, n)

    # --- after each move -----------------------------------------------------------------

    def wait_until_settled(
        self,
        scan_id,
        where: str,
        rest_g: Optional[float],
        stopped_at: float,
        min_delay_s: float,
        should_stop: Callable[[], bool],
    ) -> StabilizationOutcome:
        """Wait after a move stopped at `stopped_at` (clock time).

        Always at least `min_delay_s` (the fixed stabilization delay). With a rest
        level, then until the vibration over the last window is back under the
        threshold — at most `timeout_s` after the stop. Without a rest level, or
        when the accelerometer has no sample in the window, the fixed delay alone.
        """
        if rest_g is None:
            return self._fixed_delay(scan_id, where, stopped_at, min_delay_s, should_stop, reason=None)

        threshold_g = self.criterion.threshold_g(rest_g)
        # The window must lie entirely after the stop to judge the column at rest.
        if not self._wait_until(stopped_at + max(min_delay_s, self.criterion.window_s), should_stop):
            return StabilizationOutcome(INTERRUPTED, self._clock() - stopped_at)
        while True:
            now = self._clock()
            vibration_g, n = self._vibration(now - self.criterion.window_s, now)
            if vibration_g is None:
                return self._fixed_delay(scan_id, where, stopped_at, min_delay_s, should_stop,
                                         reason=f"accelerometer silent ({n} sample(s) in the last "
                                                f"{self.criterion.window_s:.1f} s)")
            if vibration_g <= threshold_g:
                logger.info("ColumnStabilization: scan_id=%s %s at rest after %.2f s vibration_mg=%.2f "
                            "threshold_mg=%.2f", scan_id, where, now - stopped_at, vibration_g * 1000,
                            threshold_g * 1000)
                return StabilizationOutcome(ACCELEROMETER, now - stopped_at, vibration_g, threshold_g)
            if now - stopped_at >= self.criterion.timeout_s:
                logger.warning("ColumnStabilization: scan_id=%s %s column still vibrating after %.0f s "
                               "(vibration_mg=%.2f threshold_mg=%.2f): measuring anyway", scan_id, where,
                               self.criterion.timeout_s, vibration_g * 1000, threshold_g * 1000)
                return StabilizationOutcome(TIMEOUT, now - stopped_at, vibration_g, threshold_g)
            if should_stop():
                return StabilizationOutcome(INTERRUPTED, now - stopped_at, vibration_g, threshold_g)
            self._sleep(self.POLL_S)

    def _fixed_delay(self, scan_id, where, stopped_at, min_delay_s, should_stop, reason) -> StabilizationOutcome:
        if reason is not None:
            logger.warning("ColumnStabilization: scan_id=%s %s %s: falling back to the fixed delay of %.3f s",
                           scan_id, where, reason, min_delay_s)
        if not self._wait_until(stopped_at + min_delay_s, should_stop):
            return StabilizationOutcome(INTERRUPTED, self._clock() - stopped_at)
        return StabilizationOutcome(FIXED_DELAY, self._clock() - stopped_at)
