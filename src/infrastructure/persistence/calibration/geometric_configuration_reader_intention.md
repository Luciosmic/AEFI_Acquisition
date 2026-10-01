# geometric_configuration_reader — Intention

## Rationale

Sensor calibration entries must be tagged with the sphere-mounting
geometry they were measured against (`GeometricConfigurationSignature`,
domain VO). That data used to live only in
`config_templates/aefi_device_config.json`
(`excitation.sources_geometry.sphere_diameters` /
`.pairwise_distances_ext`, the caliper measurements) — the same file
`HardwareSignatureReader` already reads for the hardware identity.

**Superseded as the live source (source geometry calibration feature):**
`SourceGeometryCalibrationService`'s append-only registry is now the source
of truth for the current geometric configuration
(`SourceGeometryCalibrationEntry.geometric_configuration`) — it carries a
full, dated, GUM-uncertainty-tracked history, unlike this reader which only
ever sees whatever is currently hand-typed into the JSON. This reader's role
shrinks to a **one-time migration/seed source**: the composition root
(`main.py`) calls it exactly once, only when
`ISourceGeometryCalibrationRepository.find_all()` is empty (first boot ever,
or a fresh `.aefi_acquisition/` directory), to mint the registry's first
entry from whatever is already in the JSON. No new config surface is
introduced by this reader itself — it still just reads the existing
template.

## Responsibility

- Read `config_templates/aefi_device_config.json` (or an injected path) and
  map its `excitation.sources_geometry` section to a
  `GeometricConfigurationSignature`.
- Tolerate a missing file, missing section, or missing individual sphere/
  distance entries by falling back to `0.0` for each missing value — never
  raise on a missing file/key itself. Unlike `HardwareSignatureReader`,
  `GeometricConfigurationSignature` has no field-level validation to lean
  on (its `__post_init__` only checks tuple arity, which fixed-length tuple
  construction always satisfies), so an all-zero signature for a missing
  config is the reader's own tolerant behavior, not a VO rejection.

## Design

- Plain `json.load`, no ORM — matches `HardwareSignatureReader`'s style.
- `DEFAULT_PATH = Path("config_templates/aefi_device_config.json")`.
- `read(path: Optional[Path] = None) -> GeometricConfigurationSignature`.
- Field mapping (`aefi_device_config.json`, `excitation.sources_geometry`):
  - `sphere_diameters_m` <- `sphere_diameters.{S1,S2,S3,S4}.value`, in that
    order.
  - `pairwise_distances_ext_m` <- `pairwise_distances_ext.{D_S1_S2,D_S3_S4,
    D_S1_S3,D_S1_S4,D_S2_S3,D_S2_S4}.value`, in that order (same order as the
    JSON template).
