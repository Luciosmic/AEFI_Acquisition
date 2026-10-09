# narda_point_already_acquired_error — Intention

## Rationale

Sans cette erreur, un second `record_samples` écraserait la mesure de champ d'un point déjà acquis et émettrait un second `NardaPointAcquired`, ce qui fausserait le comptage de la source `narda_point` du scan.

## Responsibility

- Nommer la promesse refusée : un point de champ acquis n'est plus modifiable.

## Design

- Hérite de `ValueError`, porte l'id du point (même forme que `AefiPointAlreadyAcquiredError`).
