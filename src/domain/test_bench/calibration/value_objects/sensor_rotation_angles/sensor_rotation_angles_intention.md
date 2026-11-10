# sensor_rotation_angles — Intention

## Rationale

The sensor calibration procedure (thesis vault, "Procédure de
calibration pour les angles de projection sur le banc de test") yields 3
angles (theta_x, theta_y, theta_z) of the mounting rotation P (brings the
sensor from the sources frame to its current mounting). Three floats alone are ambiguous — the same numbers mean a different
physical orientation under another rotation order or reading direction.
Without a dedicated VO carrying the angles AND their convention, a stored
triplet could be reapplied the wrong way silently.

## Responsibility

- Hold the 3 angles (degrees) and the `RotationConvention` they are
  expressed in, as a single immutable value.
- No range validation on the angles — any signed value is accepted (the
  ideal mounting is 35.26°/45°/0°, calibrated values deviate from it).
- `mounting_matrix()`: the single place that turns the angles into the
  3×3 matrix P. Without it every consumer (3D view, mock field simulator,
  …) re-derives P from the Euler string, and one lowercase `'xyz'` is
  enough to show or simulate a different mounting silently — the
  convention was already corrected twice.

## Design

- `@dataclass(frozen=True)`: `theta_x_degrees`, `theta_y_degrees`,
  `theta_z_degrees`, `convention` (defaults to `RotationConvention.standard()`,
  the only supported one).
- `mounting_matrix()` returns `P = Rx(θx)·Ry(θy)·Rz(θz)` as a numpy 3×3
  array, built literally from that definition (numpy only); its columns are
  the sensor axes expressed in the sources frame.
- Definition of P, of the frames and of the calibration procedure:
  `value_objects/rotation_convention/rotation_convention_intention.md`
  (reference — not restated here).
