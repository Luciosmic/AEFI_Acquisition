# hardware_component_characterization_entry — Intention

## Rationale

A component's properties don't drift; our knowledge of them grows (a gain
first "not characterized" gets measured). Overwriting the characterization
would lose what past acquisitions were taken with; a dated, append-only
entry per characterization keeps the history, tied together by the
component's unique name.

## Responsibility

- Bind a `ComponentCharacterization` (which carries the kind) to a unique
  `component_name` and the UTC time it was recorded.
- Refuse an empty name.

## Design

- `@dataclass(frozen=True)`, minted via `single(component_name, characterization)`;
  `kind` derived from the characterization.
- Not tagged by `HardwareSignature`: a component's characterization does not
  depend on the rest of the bench. Which component is mounted is a separate
  fact (`HardwareComponentSelection`).
