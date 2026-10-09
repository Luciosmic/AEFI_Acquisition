# fly_scan — Intention

## Rationale

Le fly-scan balaie chaque ligne d'un coup et place les points a posteriori sur la grille : il n'a pas d'`AefiPoint` par position, donc rien dans le `Scan` fin ne reference ses points. Sans cet agregat, soit `StepScan` garderait des points que le step-scan et le line-scan n'ont plus le droit de contenir (le scan est un artefact de tracage, il ne possede pas ses points), soit le fly-scan perdrait son auto-completion et son compte de points.

## Responsibility

- Garder les `ScanPointResult` du fly-scan et exposer `points` / `expected_points`.
- Auto-completer quand `expected_points` est atteint, avec `ScanCompleted(total_points=len(points))`.
- Deduire l'index de `ScanPaused` / `ScanResumed` de ses propres points.

## Design

- **Transitoire** : herite de `StepScan` et disparait a l'etape 8 du refactoring (flux `AefiLine`).
- Tout le reste du cycle de vie (start, fail, cancel, evenements) est celui de `StepScan`.
- `pause` / `resume` / `complete` ignorent l'index recu et utilisent `len(_points)` : c'est la seule source de verite d'un fly-scan.
