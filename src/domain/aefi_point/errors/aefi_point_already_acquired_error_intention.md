# aefi_point_already_acquired_error — Intention

## Rationale

Sans cette erreur, un second `record_samples` écraserait la mesure d'un point déjà acquis et émettrait un second `AefiPointAcquired`, ce qui fausserait le comptage des points d'un scan.

## Responsibility

- Nommer la promesse refusée : un point acquis n'est plus modifiable.

## Design

- Hérite de `ValueError`, porte l'id du point.
