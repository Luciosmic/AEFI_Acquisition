# component_characterization — Intention

## Rationale

A component is often mounted before all its quantities are measured (e.g.
the excitation board's gain). Forcing a number would invent one; leaving the
field out would hide the gap. Without a value object checking the values
against the kind's declared quantities, a typo in a key or a zero gain would
be persisted silently.

## Responsibility

- Hold one value per quantity of the kind: scalar > 0, curve of (x, y)
  points with x, y > 0, or `None` = not characterized.
- Refuse missing/unknown keys and non-physical values.
- `uncharacterized()`: the keys still to measure — the debt shown in the UI,
  logs and export.

## Design

- `@dataclass(frozen=True)`: `kind`, `values: Dict[str, QuantityValue]`.
- `of(kind, values)`: builds from partial values (left-out quantity = not
  characterized) and normalizes curves to tuples — used by the service and
  by persistence, so legacy entries missing a newer quantity still load.
