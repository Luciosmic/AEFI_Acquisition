---
type: atome::solidai-atome
tldr: "Nommer la promesse refusée : un scan non démarré n'accepte aucun point."
code: ["[[src/domain/scan/errors/scan_not_started_error.py]]"]
cause_de_changement: regle-metier
---
# scan_not_started_error — Intention

## Rationale

Sans ce refus, un point reçu d'un scan encore PENDING serait compté, ce qui signifie qu'un scan pourrait se compléter sans jamais avoir démarré.

## Responsibility

- Nommer la promesse refusée : un scan non démarré n'accepte aucun point.

## Design

- Hérite de `ValueError`, porte `scan_id` et `acquisition_id`.
