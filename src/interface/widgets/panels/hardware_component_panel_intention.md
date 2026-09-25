# hardware_component_panel — Intention

## Rationale

Every hardware component kind needs the same interaction — pick the mounted
component among the characterized ones, characterize a new one or complete
an existing one — and only its list of quantities differs. One panel built
from that list avoids six hand-made copies, and adding a quantity in the
domain adds its field here with no UI change. Quantities span many orders of
magnitude (nV/√Hz to MHz), so values are typed as text (scientific notation
accepted) rather than in fixed-decimal spin boxes.

## Responsibility

- "Monté sur le banc": the mounted component (orange "RIEN DE MONTÉ —
  configuration incomplète" when none, orange when a quantity is not
  characterized), a combo of characterized components, a button emitting
  `mount_requested(name)`; for boards, a reminder that a restart is needed.
- "Caractérisation": unique name + one field per quantity, each with a
  "non caractérisée" checkbox (checked by default, so nothing blocks the
  entry); curves typed as `x:y; x:y`. Emits
  `save_requested(name, {key: value | None})`; an unreadable value shows an
  error and emits nothing.
- `set_status_message(text)`: shows the presenter's feedback under the save
  button — red for `Erreur: ...` (e.g. a value refused by the domain), grey
  otherwise — so a refused entry is never silent.
- Picking a component in the combo loads its current values into the form,
  so completing it is "fill the missing value, save".

## Design

- Built from a `HardwareComponentKindDTO`; one instance per kind, added to
  `CalibrationPanel` by `add_hardware_component_tab`. No domain import.
