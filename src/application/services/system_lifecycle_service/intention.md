# System Lifecycle Service

## Rationale
Ce module orchestre les séquences de démarrage et d'arrêt du système complet. Il centralise la choreographie de l'initialisation hardware, de la vérification de connectivité et du chargement de calibration pour que l'UI, les tests et la CLI utilisent exactement le même enchaînement.

## Responsibility
- `SystemStartupApplicationService` : exécuter la séquence démarrage (initialisation hardware → vérification → chargement calibration) et publier `SystemReadyEvent` ou `SystemStartupFailedEvent`.
- `SystemShutdownApplicationService` : exécuter la séquence d'arrêt (arrêt des opérations → sauvegarde état → fermeture hardware) et publier `SystemShuttingDownEvent` / `SystemShutdownCompleteEvent`.
- Notifier l'UI via `ISystemLifecycleOutputPort` à chaque étape (started, step, error, completed).

## Design
- Services intentionnellement minces et sans état : ils délèguent toute logique hardware à `IHardwareInitializationPort`.
- Les deux services (`SystemStartupApplicationService`, `SystemShutdownApplicationService`) sont séparés par responsabilité pour respecter le SRP.
- Les dataclasses `StartupConfig`/`StartupResult` et `ShutdownConfig`/`ShutdownResult` encapsulent les paramètres et le résultat de chaque séquence.
