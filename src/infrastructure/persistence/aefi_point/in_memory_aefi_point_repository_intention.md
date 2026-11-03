# in_memory_aefi_point_repository — Intention

## Rationale

Sans implémentation de `IAefiPointRepository` branchée sur l'UoW, les événements `AefiPointAcquired` d'un point ajouté ne seraient jamais collectés au commit, ce qui signifie que le handler de Scan ne serait jamais notifié, ce qui force à publier à la main comme aujourd'hui.

## Responsibility

- Implémenter `IAefiPointRepository` en mémoire (Real et fake de test : mono-processus, sans DB ; pas de doublon fake).
- Enregistrer auprès de l'UoW chaque agrégat vu (`add`, `get`, `list_by_scan`).

## Design

- L'UoW est injectée par constructeur ; `InMemoryUnitOfWork` instancie le repository et l'expose en `aefi_points`.
- Le stockage survit au rollback (cohérent avec `InMemoryUnitOfWork` : seule la publication est annulée, l'état en mémoire n'est pas restauré).
- Logs LDD : ajout et lecture d'un id inconnu.
