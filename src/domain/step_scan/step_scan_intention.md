# step_scan — Intention

## Rationale

Aggregate Root représentant un scan 2D step-by-step en cours d'exécution. Garantit la cohérence des données de scan (ordre des points, transitions d'état valides) et produit les événements domain qui propagent les changements vers les couches supérieures.

## Responsibility

- Gérer le cycle de vie du scan : `start → (pause/resume)* → complete | fail | cancel`.
- Accumuler les `ScanPointResult` et déclencher l'auto-complétion quand `expected_points` est atteint.
- Générer et stocker les `DomainEvent` (ScanStarted, ScanPointAcquired, ScanCompleted, ScanFailed, ScanCancelled, ScanPaused, ScanResumed) via `domain_events` (get-and-clear).
- Faire respecter les invariants : impossible d'ajouter un point si le scan n'est pas `RUNNING`.

## Design

- **Hérite de `SpatialScan` (entity)** : récupère l'id UUID et les transitions d'état de base.
- **`domain_events` est get-and-clear** : le consommateur (service applicatif) vide la liste à chaque publication pour éviter les double-publications.
- **Idempotence sur `cancel()` et `pause()`** : peut être appelé plusieurs fois sans lever d'exception.
- **`_expected_points`** calculé depuis la config au `start()` : permet l'auto-complétion sans compter les points dans l'executor.
