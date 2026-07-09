# i_scan_executor — Intention

## Rationale

Abstraire la stratégie d'exécution d'un scan (synchrone, asynchrone, threading) derrière un port afin que `ScanApplicationService` reste indépendant des détails d'implémentation. Permet de substituer `StepScanExecutor` (Real) par un mock sans modifier le service.

## Responsibility

- Déclarer `execute(scan, trajectory, config) → bool` : lance l'exécution et retourne vrai si démarrée.
- Déclarer `cancel(scan)`, `pause(scan)`, `resume(scan)` : contrôle du cycle de vie en cours d'exécution.

## Design

- **Port outbound** co-localisé dans `scan_application_service/`.
- Implémenté par `StepScanExecutor` (infrastructure/execution) qui délègue sur un thread dédié avec synchronisation via `threading.Event`.
