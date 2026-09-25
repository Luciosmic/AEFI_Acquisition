# hardware_component_presenter — Intention

## Rationale

Without a presenter, each component tab would call the application service
directly and have to know when to refresh after a save or a mount.

## Responsibility

- Forward "save characterization" and "mount component" requests for its
  kind; report success/errors via `status_message` (never raises into Qt).
- Re-emit the catalog (`components_listed`) and the mounted component
  (`mounted_component_updated`, `None` = nothing mounted) whenever a
  `hardwarecomponentcharacterized` / `hardwarecomponentmounted` event
  concerns its kind.

## Design

- One instance per kind (`kind: HardwareComponentKindDTO`), all sharing one
  `HardwareComponentService`.
- Filters events by reading `event.kind` / `event.entry.kind` by attribute —
  no domain import.
