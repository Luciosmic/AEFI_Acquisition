# hardware_signature — Intention

## Rationale

Every calibration entry (synchronous detection phase today, sensor gain
later) is only valid for the specific piece of hardware it was measured on.
Mixing calibration data across board revisions or sensor units silently
corrupts measurements. `HardwareSignature` makes that scope explicit and
tags every calibration entry with it, so the repository can filter entries
by the hardware actually connected. It is read from the existing
`config_templates/aefi_device_config.json` (no new fields) via
`HardwareSignatureReader` in infrastructure — the domain VO itself has no
knowledge of that file.

## Responsibility

- Identify the excitation board, conditioning board and sensor revisions
  (plus an optional sensor serial number) a calibration entry applies to.
- Reject a signature missing any of the three required version fields —
  an incomplete signature cannot reliably distinguish hardware setups.
- Stay generic: reusable by any future calibration type, not just
  synchronous detection phase.

## Design

- `@dataclass(frozen=True)`.
- `excitation_electronics_board_name`, `conditioning_electronics_board_name`
  (`HardwareComponentName`): references, by identity, to the mounted boards
  of the hardware component catalog — not copies of their characterization
  (renamed from `*_board_version` on 2026-09-25 to say so; registries written
  before are still read, see `hardware_signature_json`).
- `sensor_version: str` — required; all three validated non-empty in
  `__post_init__`.
- `sensor_serial_number: Optional[str]` — legitimately `None` (not every
  sensor is serialized), never validated.
- Value equality (dataclass default `__eq__`) is used by
  `ISynchronousDetectionPhaseCalibrationRepository.find_by_hardware_signature`
  to match entries to the currently connected hardware.
