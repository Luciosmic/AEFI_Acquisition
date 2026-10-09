# scan_already_completed_error — Intention

## Rationale

Sans ce refus, un point inattendu reçu après complétion ferait dépasser le nombre attendu, ce qui casserait l'invariant « COMPLETED = exactement les points attendus ».

## Responsibility

- Nommer la promesse refusée : un scan complété est figé.

## Design

- Hérite de `ValueError`, porte `scan_id` et `acquisition_id`. Un id déjà reçu reste un no-op, pas une erreur.
