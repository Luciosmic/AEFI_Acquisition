# step_scan — Intention

## Rationale

Coque de cycle de vie, unique pour le step-scan, le line-scan et le fly-scan, en cours d'exécution. Le scan est un artefact de traçage : il ne possède pas ses points (ils vivent dans `AefiPoint` pour le step/line-scan et `AefiLine` pour le fly-scan, le `Scan` fin les référence par identité). Sans cette séparation, `StepScan` garderait un second état des points et un second émetteur de `ScanCompleted`. L'agrégat garantit les transitions d'état valides et produit les événements domain qui propagent les changements vers les couches supérieures.

## Responsibility

- Gérer le cycle de vie du scan : `start → (pause/resume)* → complete | fail | cancel`.
- Mettre en file `ScanPointAcquired` pour chaque point (`point_acquired`) sans le stocker ni auto-compléter.
- Suivre la complétion du `Scan` fin (`mark_completed`) : passe à `COMPLETED` sans émettre d'événement, le `ScanCompleted` étant celui du `Scan` fin.
- Générer et stocker les `DomainEvent` (ScanStarted, ScanPointAcquired, ScanFailed, ScanCancelled, ScanPaused, ScanResumed ; `ScanCompleted` n'est plus émis ici : c'est le `Scan` fin qui l'émet) via `domain_events` (get-and-clear).
- Faire respecter les invariants : impossible d'enregistrer un point si le scan n'est pas `RUNNING`.

## Design

- **Hérite de `SpatialScan` (entity)** : récupère l'id UUID et les transitions d'état de base.
- **`domain_events` est get-and-clear** : le consommateur (service applicatif) vide la liste à chaque publication pour éviter les double-publications.
- **Idempotence sur `cancel()` et `pause()`** : peut être appelé plusieurs fois sans lever d'exception.
- **Pas de points ni de total attendu** : le service compte lui-même (`_acquired_count`, `_expected_total`) et passe l'index à `pause(index)` / `resume(index)` / `complete(total_points)` (défaut 0).
- `StepScan` est l'unique coque de cycle de vie : le fly-scan l'utilise aussi (plus de sous-classe), ses points de grille étant commités par lignes (`AefiLine`).
