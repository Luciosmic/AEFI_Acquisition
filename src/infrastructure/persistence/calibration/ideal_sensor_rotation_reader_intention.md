# ideal_sensor_rotation_reader — Intention

## Rationale

The ideal (nominal) mounting angles of the sensor cube — the rotation
applied when no sensor calibration exists yet for the current source
geometry — live in `config_templates/aefi_device_config.json`
(`sensor.calibration.sources_to_sensor_rotation`, with its `convention`
block). Something has to turn that JSON into a domain `SensorRotationAngles`,
and refuse it loudly when it is incomplete or declares a convention the
application does not apply: a silently wrong rotation would corrupt every
measured field without any visible error.

## Responsibility

- Read the angles and the convention block and build a `SensorRotationAngles`
  (the `RotationConvention` VO rejects any unsupported convention).
- Raise `ValueError` if the block, an angle or the convention is missing —
  no fallback to 0/0/0, unlike `HardwareSignatureReader`'s tolerant style.

## Design

- Plain `json.load`, `DEFAULT_PATH = Path("config_templates/aefi_device_config.json")`
  (same file as `HardwareSignatureReader`/`GeometricConfigurationReader`).
- `read(path: Optional[Path] = None) -> SensorRotationAngles`.
- Called once by the composition root (`main.py`), result injected into
  `SensorCalibrationService` as `default_angles`.
- Frames and definition of the mounting rotation P (brings the sensor from the sources frame to its current mounting): `domain/calibration/value_objects/rotation_convention/rotation_convention_intention.md`.
