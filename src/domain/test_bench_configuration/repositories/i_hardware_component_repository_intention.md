# i_hardware_component_repository — Intention

## Rationale

Without a domain contract the service would read and write files itself and
could not be tested without a filesystem; the contract also pins the
append-only promise of both logs (characterizations, mountings) in one place.

## Responsibility

- `add(entry)` / `find_all(kind)`: the catalog of characterizations. Entries
  sharing a name are that component's history; the latest is current.
- `add_selection(selection)` / `find_selections(kind)`: the mounting log;
  the latest selection is the mounted component.

## Design

- One contract for every `HardwareComponentKind`.
- Real: `infrastructure/persistence/calibration/real_hardware_component_repository.py`
  (one JSON file per kind in `.aefi_acquisition/calibrations/`).
- Fake: `infrastructure/persistence/calibration/fake/fake_hardware_component_repository.py`.
