# hardware_component_dto — Intention

## Rationale

Presenters and panels must not import `domain/`. Without DTOs the generic
component tab would need `HardwareComponentKind` to know which fields to
draw, and the domain entries to display values.

## Responsibility

- `QuantitySpecDTO` / `HardwareComponentKindDTO`: what to draw for a kind.
- `HardwareComponentDTO`: one component's current characterization, with the
  list of quantities still not characterized.

## Design

- `@dataclass(frozen=True)`, primitives only; kinds are referred to by their
  string key.
