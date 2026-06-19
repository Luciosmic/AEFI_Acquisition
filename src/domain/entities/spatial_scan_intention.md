# spatial_scan — Intention

## Rationale

Entity de base pour tous les types de scan spatial (step scan, fly scan). Concentre la logique de cycle de vie d'état (PENDING → RUNNING → COMPLETED/FAILED/CANCELLED/PAUSED) et la génération d'un identifiant UUID pour chaque scan.

## Responsibility

- Générer un `id` UUID unique à la création.
- Gérer les transitions d'état via `start()`, `complete()`, `fail()`, `cancel()`, `pause()`, `resume()`.
- Faire respecter les transitions valides (ex. impossible de compléter si non RUNNING).

## Design

- **Héritée par `StepScan`** : fournit la base sans imposer le type de points.
- **`ScanStatus` enum** : les états sont typés et les transitions vérifiées — pas de chaînes libres.
- **Entity (pas Aggregate Root)** : a une identité (UUID) mais est toujours contenue dans un Aggregate Root (`StepScan`).
