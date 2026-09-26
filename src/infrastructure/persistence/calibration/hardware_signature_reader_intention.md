# hardware_signature_reader — Intention

## Rationale

Calibration entries must be tagged with the hardware setup they were
measured on (`HardwareSignature`, domain VO). That identity already lives
in `config_templates/aefi_device_config.json` — the same file
`AcquisitionSnapshotReader` bundles into export metadata — so no new
config surface is introduced. `HardwareSignatureReader` is the single
place that knows how to map that JSON's `excitation`/`sensor` sections
onto the domain VO's fields.

## Responsibility

- Read `config_templates/aefi_device_config.json` (or an injected path)
  and map it to a `HardwareSignature`.
- Tolerate a missing file or missing keys by falling back to `""` for the
  three required string fields and `None` for the optional serial number
  — never raise on a missing file/key itself.
- Let `HardwareSignature.__post_init__` be the sole source of truth on
  whether the resulting signature is valid (e.g. an entirely missing file
  yields empty required fields, which the VO itself rejects). This reader
  adds no validation of its own.

## Design

- Plain `json.load`, no ORM — matches the style of
  `hardware_config_resolution.load_json_if_exists` and
  `acquisition_snapshot_reader._load_json`.
- `DEFAULT_PATH = Path("config_templates/aefi_device_config.json")`.
- `read(path: Optional[Path] = None) -> HardwareSignature`.
- Field mapping (confirmed against the real JSON schema in
  `acquisition_snapshot_reader.py` / `config_templates/aefi_device_config.json`):
  - `excitation_electronics_board_name` <- `data["excitation"]["electronic_board_version"]`
  - `conditioning_electronics_board_name` <- `data["sensor"]["conditioning_board_version"]`
  - `sensor_version` <- `data["sensor"]["version"]`
  - `sensor_serial_number` <- `data["sensor"]["serial_number"]` (defaults to `None`)
- Since 2026-09-25, `sensor_version` / `sensor_serial_number` read here are
  only a **fallback**: `SensorCalibrationService` replaces them with the
  sensor identity of the latest sensor calibration entry (the registry is
  the source of truth), and logs a WARNING when it has to use this fallback.
- Since 2026-09-25 (later the same day), the board versions read here are
  generic template placeholders too: the mounted boards come from the
  electronic board calibration registries
  (`Calibration.resolve_current_hardware_signature`), and these names are
  only used — with a WARNING — while no board of that kind is mounted.
