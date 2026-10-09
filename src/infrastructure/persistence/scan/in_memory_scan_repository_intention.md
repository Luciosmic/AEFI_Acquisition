# in_memory_scan_repository — Intention

## Rationale

Sans implémentation de `IScanRepository` branchée sur l'UoW, les événements d'un `Scan` modifié ne seraient jamais collectés au commit, ce qui signifie que `ScanCompleted` ne serait jamais publié.

## Responsibility

- Implémenter `IScanRepository` en mémoire (Real et fake de test : mono-processus, sans DB).
- Enregistrer auprès de l'UoW chaque agrégat vu (`add`, `get`).

## Design

- L'UoW est injectée par constructeur ; `InMemoryUnitOfWork` l'expose en `scans`.
- Le stockage survit au rollback (comme `InMemoryAefiPointRepository`).
- Logs LDD : ajout et lecture d'un id inconnu.
