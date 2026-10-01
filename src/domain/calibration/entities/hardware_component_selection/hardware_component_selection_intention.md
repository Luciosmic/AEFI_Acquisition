# hardware_component_selection — Intention

## Rationale

Characterizing a component and mounting it are two facts with two causes of
change: measurement vs. module swap. If "latest characterization recorded"
meant "mounted", completing a spare board's gain would silently declare it
mounted. A separate, append-only mounting log keeps them apart and answers
"which component was on the bench on that date".

## Responsibility

- Record one component (kind + name) declared mounted, with the UTC time.
- Refuse an empty name.

- Give each mounting its own identity (`mounting_id`): a sensor's angle
  calibration is only valid for the mounting it was measured on —
  unmounting and remounting the same sensor can change its orientation.

## Design

- `@dataclass(frozen=True)`: `kind`, `component_name`, `selected_at`, `mounting_id`;
  `now(kind, name)` factory. Minted by `Calibration.mount_hardware_component`,
  which checks the component is characterized.
