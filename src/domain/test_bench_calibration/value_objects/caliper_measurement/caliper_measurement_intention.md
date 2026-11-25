---
type: value-object::solidai-ddd
tldr: "Hold one measured value with its GUM expanded uncertainty (`U = k*u_c`) and the coverage factor `k` used to compute it."
code: ["[[src/domain/test_bench_calibration/value_objects/caliper_measurement/caliper_measurement.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/test_bench_calibration/calibration_intention]]"
---
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
- `__post_init__` rejects a non-finite or non-positive `value_m` (a caliper
  never reads 0 or a negative length), and a non-finite
  or negative `uncertainty_expanded_m`/non-positive `k`.
- `from_resolution(value_m, resolution_m=0.00002, k=2.0)`: `u_c = resolution_m / (2*sqrt(3))`
  (rectangular/uniform distribution, single reading at instrument
  resolution — the same GUM convention documented in
  `aefi_device_config.json`'s `_note` fields), `uncertainty_expanded_m = k * u_c`.
  Defaults (0.02mm vernier, k=2) reproduce the values already hand-written
  throughout the existing JSON (`1.15e-5` m expanded uncertainty).
- `uniform_half_width_m: Optional[float] = None`: the half-width `a` of the
  uniform law behind the uncertainty, or None when the uncertainty was given
  directly. When set, `__post_init__` requires `U = k*a/sqrt(3)`.
  Why: on 2026-11-24 the six distances of the compression mount disagreed by
  up to 250 µm, so a distance is no longer known to the vernier resolution;
  the operator states the half-width (±0.25 mm for distances, ±0.01 mm for
  diameters) and the calibration must carry it.
- `from_uniform_half_width(value_m, half_width_m=0.01mm, k=2.0)`: `u_c = a/sqrt(3)`.
  The default equals `from_resolution`'s default (`0.02mm/(2*sqrt(3))`), so
  past calibrations keep their uncertainty. `from_resolution` records
  `a = resolution/2`.
- `from_uniform_expanded_uncertainty(value_m, U, k)`: keeps `U` and recovers
  `a = sqrt(3)*U/k` — how a reading stored before the half-width existed is read back.
