# hardware_component_dto — Intention

## Rationale

Presenters and panels must not import `domain/`. Without DTOs the generic
component tab would need `HardwareComponentKind` to know which fields to
draw, and the domain entries to display values.

## Responsibility

- `QuantitySpecDTO` / `HardwareComponentKindDTO`: what to draw for a kind.
- `RecordCharacterizationResultDTO`: non-blocking outcome of a recording
  (name already in the catalog), so the UI can warn without domain access.
- `HardwareComponentDTO`: one component's current characterization, with the
  list of quantities still not characterized.

## Design

- `@dataclass(frozen=True)`, primitives only; kinds are referred to by their
  string key.
