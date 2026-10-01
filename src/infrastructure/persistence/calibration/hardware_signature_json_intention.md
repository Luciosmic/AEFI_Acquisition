# hardware_signature_json — Intention

## Rationale

Two registries (synchronous detection phase, sensor calibration) persist a
`HardwareSignature`. Each used to hand-write the same four keys; renaming the
board fields into component references would have had to be done — and kept
in sync — in both, and a registry written with the old key names would have
become unreadable.

## Responsibility

- `hardware_signature_to_json`: write the board references under
  `excitation_electronics_board_name` / `conditioning_electronics_board_name`.
- `hardware_signature_from_json`: read them, falling back to the keys written
  before 2026-09-25 (`excitation_board_version` / `conditioning_board_version`),
  so existing phase and sensor calibrations stay readable. The sensor is a
  catalog component referenced by `sensor_name`; signatures written before
  carried `sensor_version` + `sensor_serial_number`, read as the component
  name `"<version>_<serial>"` (or `"<version>"` without serial number).

## Design

- Two plain functions; no class, no state.
