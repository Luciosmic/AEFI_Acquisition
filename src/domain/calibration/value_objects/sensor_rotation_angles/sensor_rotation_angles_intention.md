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

## Design

- `@dataclass(frozen=True)`: `theta_x_degrees`, `theta_y_degrees`,
  `theta_z_degrees`, `convention` (defaults to `RotationConvention.standard()`,
  the only supported one).
- Definition of P, of the frames and of the calibration procedure:
  `value_objects/rotation_convention/rotation_convention_intention.md`
  (reference — not restated here).
