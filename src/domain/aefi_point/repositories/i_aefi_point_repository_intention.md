# i_aefi_point_repository — Intention

## Rationale

Sans port de persistance, le comptage des points d'un scan passe par l'état du service applicatif, ce qui signifie que le `Scan` dépend des détails de collecte, ce qui force à modifier la boucle de scan à chaque évolution du handler.

## Responsibility

- `add(point)`, `get(point_id)`, `list_by_scan(scan_id)` (comptage des points d'un scan).

## Design

- ABC placée dans `domain/aefi_point/repositories/` (convention `calibration/repositories/`).
- Chaque implémentation appelle `uow.register(point)` sur les agrégats qu'elle voit.
