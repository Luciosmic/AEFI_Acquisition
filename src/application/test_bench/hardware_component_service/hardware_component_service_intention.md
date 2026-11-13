# hardware_component_service — Intention

## Rationale

The bench's hardware — boards, signal generation chip, ADC, microcontroller,
motors — is made of product modules whose essential physical quantities must
be known to interpret a measurement, and which are swapped independently.
Without this service each module's characteristics would live in a notebook
or a hand-edited JSON template, the mounted module would be implicit, and
nothing would tie an acquisition to the hardware it was taken with. It also
lets a module be mounted before all its quantities are measured, recording
the gap instead of blocking the work.

## Responsibility

- `list_kinds()`: the component kinds and their quantities (for the UI).
- `record_characterization(kind_key, name, values)`: append a
  characterization (new component, or completion of an existing one's
  history); missing values are recorded as not characterized, with a WARNING.
- `mount_component(kind_key, name)`: declare the mounted component — refused
  if never characterized, logged no-op if already mounted. Mounting a board
  warns that other calibrations only follow after a restart.
- `list_components(kind_key)` / `get_mounted_component(kind_key)`: the
  catalog, and the mounted component (None + WARNING if none: incomplete
  configuration).
- `get_mounted_component_name(kind_key)` (composition root only): feeds
  `Calibration.resolve_current_hardware_signature` for the two boards.

## Design

- One service for every `HardwareComponentKind`; rules live in the
  `Calibration` aggregate (`record_hardware_component_characterization`,
  `mount_hardware_component`, `mounted_component_name`,
  `current_characterization`).
- Inbound API speaks string kind keys and DTOs only.
- Topics: `hardwarecomponentcharacterized`, `hardwarecomponentmounted`.
