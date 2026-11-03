# scan_already_started_error — Intention

## Rationale

Sans ce refus, un second `start()` rouvrirait un scan déjà démarré ou complété, ce qui fausserait l'état observable.

## Responsibility

- Nommer la promesse refusée : seul un scan PENDING démarre.

## Design

- Hérite de `ValueError`, porte `scan_id`.
