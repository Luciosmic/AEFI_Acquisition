# rotation_convention — Intention

**This file is the reference definition of the sensor rotation convention.**
The JSON device config (`sensor.calibration.sources_to_sensor_rotation`),
the code docstrings and the thesis vault note ("Procédure de calibration
pour les angles de projection sur le banc de test") point here instead of
restating it.

## Rationale

The same three angles (theta_x, theta_y, theta_z) were read in
incompatible ways: scipy uppercase (intrinsic) and lowercase (extrinsic)
axis strings were confused, the reading direction (sensor → sources or
sources → sensor) flipped between code and notes, and "lab" meant
sometimes the bench, sometimes the sources. Without one frozen definition,
an angle triplet recorded today can be applied the wrong way tomorrow —
silently, since any rotation "looks" plausible — and measured fields end
up expressed in a frame nobody intended.

This actually happened, twice. The convention was corrected two times in
a row, because the mirror orientation cannot be told apart from the right
one by geometry alone: both put the cube on a vertex and both look
plausible. It was settled by measurement on 2026-09-25: the previous code
required NEGATIVE angles to bring the signals back to the sources frame,
and negating the angles in that previous transform gives exactly `P(θ)`
as defined below.

Warning: transposing is NOT negating the angles. Transposing also reverses
the order of the elementary rotations:

    Pᵀ = Rz(−θz) · Ry(−θy) · Rx(−θx)    ≠    P(−θ) = Rx(−θx) · Ry(−θy) · Rz(−θz)

## Vocabulary — frames

- **sensor frame (repère capteur)**: axes of the cube faces/electrodes.
  The sensor reads `E_sensor = (E_x^sensor, E_y^sensor, E_z^sensor)` in
  this frame.
- **sources frame (repère sources)**: frame of the 4 excitation spheres.
  The sensor is positioned relative to the sources — this is the frame the
  calibration refers to.
- **bench frame (repère banc)**: motion axes of the column (XY scan).
  Assumed identical to the sources frame (bench ≡ sources).
- "lab" is **not** part of the vocabulary: it used to mean either bench or
  sources.

Notation: every vector carries its frame. Components are written
`E_sensor`, `E_sources`; basis vectors `e_x^sensor`, `e_z^sources`. A bare
`e_z` is never written.

## Definition of P (mounting angles)

    P = Rx(theta_x) · Ry(theta_y) · Rz(theta_z)

- **Extrinsic**: rotations about the FIXED sources axes, **applied first
  about Z, then Y, then X** (`order = "ZYX"`) — equivalently intrinsic
  X → Y' → Z''.
- In scipy: `Rotation.from_euler('XYZ', [theta_x, theta_y, theta_z], degrees=True)`
  — **UPPERCASE** letters (intrinsic in scipy). Lowercase axis letters
  would be a DIFFERENT rotation.
- **Meaning of P**: P brings the sensor, initially aligned with the
  sources frame, to its current mounting. The columns of P are the sensor
  axes `e_i^sensor` expressed in the sources frame.
- Elementary matrices are the standard right-handed ones, e.g.
  `Rz(a) = [[cos a, -sin a, 0], [sin a, cos a, 0], [0, 0, 1]]`.
- The angles are entered as they are — never negated.

## Signals (`direction = "sources_to_sensor"`)

    E_sensor  = Pᵀ · E_sources      (measurement: what the sensor reads of a given field)
    E_sources = P  · E_sensor       (coordinate transform: "Apply Rotation", export post-processing)

The coordinate transform is the transpose of the measurement.

## Ideal mounting

With the ideal angles (35.264°, 45°, 0°) — written 35.3 in the device
config — `P·(−1, 1, 1)/√3 = (0, 0, 1)`, i.e.

    e_z^sources = (−e_x^sensor + e_y^sensor + e_z^sensor) / √3

The sources vertical is a cube diagonal: the cube stands on a vertex.

To draw the cube in the sources frame, its vertices (known in the sensor
frame) are converted with `P` — the same formula as the coordinate
transform of the signals.

## Calibration procedure

The angles are found by trial and error on the signal brought back to the
sources frame (`E_sources = P·E_sensor`):

- excitation along X → `E_x^sources` max, `E_y^sources` and `E_z^sources` min;
- excitation along Y → `E_y^sources` max, `E_x^sources` and `E_z^sources` min.

There is **no closed-form formula**: closed forms assume a uniform,
perfectly oriented primary field, which is false on the bench because of
the asymmetries of the sphere mounting.

Trial angles are applied live through `SensorCalibrationService.preview_rotation`
and persisted only when recorded ("Enregistrer calibration"). "Reset to
Default" restarts from the ideal angles. A future automatic calibration
service will optimize the same criterion by driving the same preview.

## Relation to the thesis vault note

The note "Procédure de calibration pour les angles de projection sur le
banc de test" writes `E_probe = Rz·Ry·Rx(θ_note)·E_bench`, with
`E_probe = E_sensor` and `E_bench = E_sources`. This equals
`Pᵀ(θ)·E_sources` if and only if `θ_note = −θ_ui`: the note's angles are
the opposite of the angles entered in the application. Its closed-form
formulas hold only for an ideal primary field. Its printed `R_z` matrix
still has a sign typo (`[[cos, sin], [sin, cos]]` instead of
`[[cos, -sin], [sin, cos]]`).

## Responsibility

- Name the convention attached to every stored angle triplet
  (`SensorRotationAngles.convention`), so an entry stays interpretable on
  its own.
- Reject any other convention.

## Design

- `@dataclass(frozen=True)`: `type`, `order`, `direction` (plain strings,
  same values as the JSON `convention` block).
- `RotationConvention.standard()` = `("extrinsic", "ZYX", "sources_to_sensor")`.
  This triple differs from both previous ones (the last being
  `("extrinsic", "XYZ", "sources_to_sensor")`), so an entry recorded under
  an older convention is rejected, never silently re-read.
- `__post_init__` raises `ValueError` for anything else — supporting
  another convention means adding the matching math in
  `TransformationService`, not just accepting a new string.
