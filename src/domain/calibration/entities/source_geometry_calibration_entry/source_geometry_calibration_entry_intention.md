# source_geometry_calibration_entry — Intention

## Rationale

Mirrors `SensorCalibrationEntry`'s shape (immutable, timestamped,
minted via a `single()` factory) for the source geometry's own calibration
type on the same `Calibration` aggregate — but with an added invariant
check that neither `SensorCalibrationEntry` nor the raw
`GeometricConfigurationSignature` snapshot enforce: a caliper transcription
error (e.g. swapped digits) can silently produce spheres that would
physically overlap. `external_modules/source_geometry/source_geometry.py`
already protects this exact invariant for its own standalone `SourceGeometry`
VO — this entity re-derives the same check so a bad entry is rejected at
recording time, not discovered later when `external_modules/source_geometry/`
happens to be run manually.

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
- `__post_init__` checks tuple arity (4 and 6) then, for each distance,
  `distance.value_m - r_i - r_j > 0` — same formula as
  `SourceGeometry.__post_init__` in `external_modules/source_geometry/`,
  re-derived here rather than imported (that module is deliberately kept
  outside `src/`, not yet a dependency of the app per its own README).
- `single(sphere_diameters, pairwise_distances_ext)` static factory —
  `entry_id=uuid4()`, `recorded_at=datetime.now(timezone.utc)`.
