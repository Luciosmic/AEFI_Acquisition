# aefi_point_id — Intention

## Rationale

Avec des `UUID` bruts, l'identité d'un point et celle d'un scan sont interchangeables pour le vérificateur de types, ce qui laisse passer `repo.get(scan_id)` sans erreur.

## Responsibility

- Typer l'identité d'un `AefiPoint`.

## Design

- `NewType` sur `UUID` (convention `HardwareComponentName`) ; le cast se fait aux frontières du domaine : `AefiPointId(uuid4())`.
