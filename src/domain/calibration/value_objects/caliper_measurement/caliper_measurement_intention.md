# caliper_measurement — Intention

## Rationale

The source geometry calibration procedure records 10 raw caliper readings
(4 sphere diameters + 6 extremity-to-extremity distances), each of which
needs a value AND a GUM expanded uncertainty. Today that uncertainty is
computed by hand once and typed directly into `aefi_device_config.json` —
no code reproduces the formula anywhere in the repo. Without this VO, the
value+uncertainty+k triplet would be duplicated 10 times as loose
parameters or a dict, and the GUM formula would have to be re-derived by
hand again for every future re-measurement.

## Responsibility

- Hold one measured value with its GUM expanded uncertainty (`U = k*u_c`)
  and the coverage factor `k` used to compute it.
- Compute the expanded uncertainty from an instrument resolution via
  `from_resolution(...)`, so a re-measurement never requires hand-deriving
  the formula again.

## Design

- `@dataclass(frozen=True)`: `value_m`, `uncertainty_expanded_m`, `k`.
- `__post_init__` rejects a non-finite or non-positive `value_m`
  (mirrors `SourceGeometry._RAW_FIELDS` validation in
  `external_modules/source_geometry/source_geometry.py`), and a non-finite
  or negative `uncertainty_expanded_m`/non-positive `k`.
- `from_resolution(value_m, resolution_m=0.00002, k=2.0)`: `u_c = resolution_m / (2*sqrt(3))`
  (rectangular/uniform distribution, single reading at instrument
  resolution — the same GUM convention documented in
  `aefi_device_config.json`'s `_note` fields), `uncertainty_expanded_m = k * u_c`.
  Defaults (0.02mm vernier, k=2) reproduce the values already hand-written
  throughout the existing JSON (`1.15e-5` m expanded uncertainty).
