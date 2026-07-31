# Point Charge Field Simulator — Intention

## Rationale

Simulates the electrostatic potential produced by the 4 excitation spheres,
for use by the mock acquisition port when no real hardware is connected.
Replaces the earlier heuristic (a static per-`ExcitationMode` offset vector)
with a physically grounded model: each sphere is a point/charged-sphere
source, and any point in space sees the superposition of their individual
potentials.

Perfect-square simplification (deliberate, per user decision 2026-07-31):
sphere positions are derived assuming an exact square (no DGP best-fit), so
all 4 spheres are equidistant from the square's geometric center. This model
has no notion of an object under test — it is the empty-bench baseline — so
`ExcitationMode` has no effect on the result: only the two independent DDS
pair levels (`level_s1_s2`, `level_s3_s4`) do.

Pure geometry+physics only — knows nothing about a sensor (position, size,
orientation). `CubeSensorFieldSimulator` (co-located) is the consumer that
samples this potential field at a finite sensor's face points.

## Responsibility

- Convert a DDS pair level (%) to its driven RMS voltage (10% = 10.6V,
  linear to 100%).
- Model each sphere as a charged conducting sphere: `V(r) = V0 * R / r`
  outside its surface, sign from `SphereId.is_direct_output` (differential
  pair polarity).
- Expose `potential_at(point, ...)`: the summed potential (V) at an
  arbitrary source-frame point — the primitive `CubeSensorFieldSimulator`
  calls repeatedly to average over a sensor face.
- Derive sphere positions (center-to-sensor distance + quadrant sign, per-
  sphere radius) from `aefi_device_config.json`'s measured diagonals and
  diameters — no dependency on `external_modules/source_geometry` (that DGP
  solver is a calibration tool, not a runtime dependency of `src/`).

## Design

- Pure calculation class, no side effects beyond reading its input config
  dict at construction (`from_config`). Lives in `infrastructure/mocks/`
  because it's simulation-only infrastructure, not real domain behavior.
