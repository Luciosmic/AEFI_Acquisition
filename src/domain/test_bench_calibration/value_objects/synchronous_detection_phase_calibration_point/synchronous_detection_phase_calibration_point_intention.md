# synchronous_detection_phase_calibration_point — Intention

## Rationale

The residual phase offset between the excitation reference (ch1) and the
synchronous-detection reference (ch3) — Delta_Phi — drifts with excitation
frequency because it originates in the external electronics (cabling,
amplifiers) downstream of the AD9106, not in the chip's internal phase
reference. A single calibration point captures Delta_Phi at one frequency
so the application layer can later look up (nearest-neighbor) the
correction to apply at any operating frequency.

## Responsibility

- Associate a frequency (Hz) with the signed phase delta (degrees) measured
  at that frequency.
- Reject a non-positive frequency — a calibration point only makes sense
  for an actual excitation frequency.
- Allow a negative delta: this is a signed offset (ch3 - ch1), not an
  absolute angle, so it is deliberately not modeled as a `PhaseAngle`
  (which wraps to [0, 360)).

## Design

- `@dataclass(frozen=True)`.
- `frequency_hz: float` — validated `> 0` in `__post_init__`.
- `delta_phi_degrees: float` — signed, unvalidated (any real value is a
  legitimate measured delta).
