# in_memory_aefi_line_repository — Intention

## Rationale

Sans implémentation de `IAefiLineRepository` branchée sur l'UoW, les événements `AefiLineAcquired` d'une ligne ajoutée ne seraient jamais collectés au commit, ce qui signifie que le handler de Scan ne serait jamais notifié, ce qui force à publier à la main comme aujourd'hui.

## Responsibility

- Implémenter `IAefiLineRepository` en mémoire (Real et fake de test : mono-processus, sans DB).
- Enregistrer auprès de l'UoW chaque agrégat vu (`add`, `get`, `list_by_scan`) ; `list_by_scan` trie par `line_index`.

## Design

- L'UoW est injectée par constructeur ; `InMemoryUnitOfWork` instancie le repository et l'expose en `aefi_lines`.
- Le stockage survit au rollback (comme `InMemoryAefiPointRepository`).
- Logs LDD : ajout et lecture d'un id inconnu.
