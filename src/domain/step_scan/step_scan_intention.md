# step_scan — Intention

## Rationale

Coque de cycle de vie d'un step-scan ou line-scan en cours d'exécution. Le scan est un artefact de traçage : il ne possède pas ses points (ils vivent dans `AefiPoint`, le `Scan` fin les référence par identité). Sans cette séparation, `StepScan` garderait un second état des points et un second émetteur de `ScanCompleted`. L'agrégat garantit les transitions d'état valides et produit les événements domain qui propagent les changements vers les couches supérieures.

## Responsibility

- Gérer le cycle de vie du scan : `start → (pause/resume)* → complete | fail | cancel`.
- Mettre en file `ScanPointAcquired` pour chaque point (`point_acquired`) sans le stocker ni auto-compléter.
- Suivre la complétion du `Scan` fin (`mark_completed`) : passe à `COMPLETED` sans émettre d'événement, le `ScanCompleted` étant celui du `Scan` fin.
- Générer et stocker les `DomainEvent` (ScanStarted, ScanPointAcquired, ScanFailed, ScanCancelled, ScanPaused, ScanResumed ; `ScanCompleted` seulement via `complete()`, utilisé par `FlyScan`) via `domain_events` (get-and-clear).
- Faire respecter les invariants : impossible d'enregistrer un point si le scan n'est pas `RUNNING`.

## Design

- **Hérite de `SpatialScan` (entity)** : récupère l'id UUID et les transitions d'état de base.
- **`domain_events` est get-and-clear** : le consommateur (service applicatif) vide la liste à chaque publication pour éviter les double-publications.
- **Idempotence sur `cancel()` et `pause()`** : peut être appelé plusieurs fois sans lever d'exception.
- **Pas de points ni de total attendu** : le service compte lui-même (`_acquired_count`, `_expected_total`) et passe l'index à `pause(index)` / `resume(index)` / `complete(total_points)` (défaut 0).
- **`FlyScan(StepScan)`** (`fly_scan.py`) garde les points et l'auto-complétion du fly-scan ; transitoire jusqu'à l'étape 8 (`AefiLine`).
