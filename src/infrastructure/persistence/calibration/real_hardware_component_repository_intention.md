# real_hardware_component_repository — Intention

## Rationale

The component catalog (characterization history per unique name) and the
mounting log must survive restarts and stay readable outside the
application. One file per kind keeps each registry small and readable, and a
single adapter keeps the format identical for every kind.

## Responsibility

- Persist, per `HardwareComponentKind`, in
  `.aefi_acquisition/calibrations/<kind>_calibration.json`:
  `{"entries": [{entry_id, component_name, characterization{key: value},
  recorded_at}], "selections": [{component_name, selected_at}]}`.
  `null` = not characterized (always written); curves as `[[x, y], ...]`.
- Treat a missing or corrupt file as empty (logged).
- Read the formats written earlier the same day, so no bench data is lost:
  - `response` instead of `characterization`, `board_name` instead of
    `component_name`;
  - entries tagged by a full `hardware_signature` (name = its board field);
  - `excitation_electronic_board_calibration.json` (kind since renamed
    `excitation_electronics_board`): read while the new file doesn't exist;
    the first write creates the new file with its content, migrating it.
- Ignore (WARNING) persisted quantities no longer declared for the kind.

## Design

- Plain JSON, no ORM, same style as the other calibration registries.
