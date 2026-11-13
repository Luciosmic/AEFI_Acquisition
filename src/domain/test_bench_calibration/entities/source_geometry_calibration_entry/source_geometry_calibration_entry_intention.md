# source_geometry_calibration_entry — Intention

## Rationale

Mirrors `SensorCalibrationEntry`'s shape (immutable, timestamped,
minted via a `single()` factory) for the source geometry's own calibration
type on the same `Calibration` aggregate — but with an added invariant
check that neither `SensorCalibrationEntry` nor the raw
`GeometricConfigurationSignature` snapshot enforce: a caliper transcription
error (e.g. swapped digits) can silently produce spheres that would
physically overlap. This entity rejects such an entry at recording time, and
is the single input of `SourceFrameSolver` (center positions
reconstruction) — one vocabulary and one distance order for the whole
source geometry, replacing the former `external_modules/source_geometry/`
`SourceGeometry` VO (`D_12, D_13, …` order).

## Responsibility

- Bundle 4 sphere-diameter `CaliperMeasurement`s (S1..S4) and 6
  extremity-to-extremity distance `CaliperMeasurement`s (same field order as
  `GeometricConfigurationSignature`: D_S1_S2, D_S3_S4, D_S1_S3, D_S1_S4,
  D_S2_S3, D_S2_S4) with the timestamp of the measurement.
- Reject a geometry where any measured distance is not strictly greater than
  the sum of the two relevant sphere radii — physically impossible
  (overlapping spheres), so almost certainly a data-entry error.
- Expose `geometric_configuration`, mapping to the pre-existing
  `GeometricConfigurationSignature` VO (raw values only, uncertainty
  dropped) — the bridge this registry needed to become the live source
  consumed by `SensorCalibrationService`.

## Design

- `@dataclass(frozen=True)`, mirrors `SensorCalibrationEntry` field-for-
  field except a single `angles` field becomes two `CaliperMeasurement`
  tuples (4 and 6).
- `_DISTANCE_SPHERE_PAIRS`: static index mapping (into `sphere_diameters`,
  0-based) for each of the 6 `pairwise_distances_ext` slots — the same
  D_ij <-> (sphere i, sphere j) pairing already fixed by
  `GeometricConfigurationReader`/`aefi_device_config.json`.
- `center_to_center_distances_m`: `{(i, j): D_ij - r_i - r_j}` in
  `pairwise_distances_ext` order — the only place the D_ij <-> sphere pair
  mapping is applied; `SourceFrameSolver` and the export read it.
- `__post_init__` checks tuple arity (4 and 6, `ValueError`: programmer
  error) then that every center-to-center distance is `> 0`, raising
  `SourceGeometryInconsistentError` naming the offending `D_Si_Sj`.
- `single(sphere_diameters, pairwise_distances_ext)` static factory —
  `entry_id=uuid4()`, `recorded_at=datetime.now(timezone.utc)`.
