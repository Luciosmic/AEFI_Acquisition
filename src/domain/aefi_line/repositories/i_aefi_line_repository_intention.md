# i_aefi_line_repository — Intention

## Rationale

Sans port de persistance, le comptage et la relecture des lignes d'un scan passent par l'état du service applicatif, ce qui signifie que le `Scan` et l'export dépendent des détails de la boucle fly, ce qui force à la modifier à chaque évolution du handler.

## Responsibility

- `add(line)`, `get(line_id)`, `list_by_scan(scan_id)` (trié par `line_index`).

## Design

- ABC placée dans `domain/aefi_line/repositories/`, comme `IAefiPointRepository`.
- Chaque implémentation appelle `uow.register(line)` sur les agrégats qu'elle voit.
