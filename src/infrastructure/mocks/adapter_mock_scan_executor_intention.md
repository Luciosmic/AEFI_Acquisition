# adapter_mock_scan_executor — Intention

## Rationale

Mock de `IScanExecutor` pour tester `ScanApplicationService` en isolation complète de l'infrastructure d'exécution. Simule une exécution de scan immédiate sans threads ni hardware.

## Responsibility

- Implémenter `execute()` en publiant directement `ScanStarted`, `ScanPointAcquired` (N fois), `ScanCompleted` sur le bus.
- Implémenter `cancel()`, `pause()`, `resume()` comme no-ops ou avec enregistrement pour assertions.

## Design

- **Synchrone** : tout se passe dans le thread appelant — pas de threads ni async.
- Permet de tester le forwarding d'événements vers `IScanOutputPort` dans `ScanApplicationService`.
