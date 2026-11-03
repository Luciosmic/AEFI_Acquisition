# i_narda_point_repository — Intention

## Rationale

Sans port de persistance, le commit d'un point de champ ne publierait jamais `NardaPointAcquired` après transaction, et le `Scan` ne saurait pas que ses mesures de champ sont complètes.

## Responsibility

- `add(point)`, `get(point_id)`, `list_by_scan(scan_id)`.

## Design

- ABC placée dans `domain/narda_point/repositories/` (même forme que `IAefiPointRepository`).
- Chaque implémentation appelle `uow.register(point)` sur les agrégats qu'elle voit.
