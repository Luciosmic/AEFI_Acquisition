"""
Fly Scan Line Projector - Domain Service

Responsibility:
- Place, live, the samples of one fly-scan line on its grid points using the
  positions reported by the motion controller while the line is swept: the
  instant the trace crosses a grid point, then the samples at that instant.
- Emit each grid point as soon as the trace has passed it and a later sample
  has arrived; place the rest when the line ends.

Rationale:
- A fly scan is a quick exploration: software timestamps, positions every
  ~150 ms — imperfect synchronization, accepted (see the intention file).
"""

from bisect import bisect_left
from typing import List, Optional, Tuple

from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement

_COMPONENTS = (
    "voltage_x_in_phase", "voltage_x_quadrature",
    "voltage_y_in_phase", "voltage_y_quadrature",
    "voltage_z_in_phase", "voltage_z_quadrature",
)

GridPoint = Tuple[int, AefiVoltageMeasurement]


class FlyScanLineProjector:
    """Live placement of one fly-scan line from its position trace (one instance per line)."""

    def __init__(self, n_points: int, line_length_mm: float):
        if n_points < 2:
            raise ValueError(f"A fly-scan line needs at least 2 points, got {n_points}")
        if line_length_mm <= 0:
            raise ValueError(f"line_length_mm must be > 0, got {line_length_mm}")
        spacing_mm = line_length_mm / (n_points - 1)
        self._abscissas = [k * spacing_mm for k in range(n_points)]
        self._trace: List[Tuple[float, float]] = []  # (t, abscissa), abscissa non-decreasing
        self._sample_times: List[float] = []
        self._samples: List[AefiVoltageMeasurement] = []
        self._next = 0

    def add_position(self, t: float, abscissa_mm: float) -> List[GridPoint]:
        """A position reported at instant t, as an abscissa along the line (mm)."""
        if self._trace and abscissa_mm < self._trace[-1][1]:
            return []  # a sweep goes one way: ignore jitter backwards
        self._trace.append((t, abscissa_mm))
        return self._ready_points()

    def add_sample(self, t: float, measurement: AefiVoltageMeasurement) -> List[GridPoint]:
        """A sample received at instant t."""
        self._sample_times.append(t)
        self._samples.append(measurement)
        return self._ready_points()

    def finish(self) -> List[GridPoint]:
        """Line ended: remaining points at their crossing instant if the trace
        has one, else at the trace's last instant; nearest sample if none follows."""
        if not self._samples:
            raise ValueError("No sample received during the line: nothing to place on its points")
        remaining = []
        for k in range(self._next, len(self._abscissas)):
            t_k = self._crossing_time(self._abscissas[k])
            if t_k is None:
                t_k = self._trace[-1][0] if self._trace else self._sample_times[-1]
            remaining.append((k, self._value_at(t_k)))
        self._next = len(self._abscissas)
        return remaining

    def _ready_points(self) -> List[GridPoint]:
        ready = []
        while self._next < len(self._abscissas):
            t_k = self._crossing_time(self._abscissas[self._next])
            if t_k is None or not self._sample_times or self._sample_times[-1] < t_k:
                break
            ready.append((self._next, self._value_at(t_k)))
            self._next += 1
        return ready

    def _crossing_time(self, abscissa_mm: float) -> Optional[float]:
        """First instant the trace reaches abscissa_mm (linear between positions), None if not yet."""
        for i, (t, s) in enumerate(self._trace):
            if s >= abscissa_mm:
                if i == 0:
                    return t
                t_a, s_a = self._trace[i - 1]
                return t_a + (t - t_a) * (abscissa_mm - s_a) / (s - s_a)
        return None

    def _value_at(self, t: float) -> AefiVoltageMeasurement:
        after = bisect_left(self._sample_times, t)
        if after == 0:
            return self._samples[0]
        if after == len(self._samples):
            return self._samples[-1]
        t_a, t_b = self._sample_times[after - 1], self._sample_times[after]
        a, b = self._samples[after - 1], self._samples[after]
        weight = (t - t_a) / (t_b - t_a) if t_b > t_a else 0.0
        return AefiVoltageMeasurement(
            **{c: getattr(a, c) + weight * (getattr(b, c) - getattr(a, c)) for c in _COMPONENTS},
            timestamp=b.timestamp,
        )
