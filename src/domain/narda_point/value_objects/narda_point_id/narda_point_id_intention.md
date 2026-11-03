# narda_point_id — Intention

## Rationale

Avec des `UUID` bruts, l'identité d'un point de champ électrique, celle d'un point AEFI et celle d'un scan sont interchangeables pour le vérificateur de types, ce qui laisse passer `repo.get(scan_id)` sans erreur.

## Responsibility

- Typer l'identité d'un `NardaPoint`.

## Design

- `NewType` sur `UUID` (même forme que `AefiPointId`) ; le cast se fait aux frontières du domaine : `NardaPointId(uuid4())`.
