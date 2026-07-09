# system_lifecycle_service — Intention

## Rationale

Centraliser les séquences de démarrage et d'arrêt du système AEFI afin que la UI, les tests et les scripts CLI utilisent la même chorégraphie. Sans ce service, les séquences seraient dupliquées ou éparpillées dans la présentation. Deux services distincts (`SystemStartupApplicationService` / `SystemShutdownApplicationService`) évitent une classe trop chargée.

## Responsibility

**SystemStartupApplicationService** :
- Initialiser le hardware via `IHardwareInitializationPort`.
- Vérifier optionnellement la connectivité.
- Charger la dernière calibration si un service de calibration est fourni.
- Publier `SystemReadyEvent` ou `SystemStartupFailedEvent` sur `IDomainEventBus`.
- Notifier la UI via `ISystemLifecycleOutputPort` à chaque étape.

**SystemShutdownApplicationService** :
- Arrêter les opérations actives (scan, acquisition).
- Optionnellement persister l'état.
- Fermer les connexions hardware.
- Publier `SystemShuttingDownEvent` / `SystemShutdownCompleteEvent`.

## Design

- **Services stateless** : aucun état interne, toute la logique passe par les collaborateurs injectés.
- **`IHardwareInitializationPort`** abstrait la connaissance des drivers concrets.
- **Erreurs non-fatales** : les exceptions sont capturées, accumulées dans `errors`, et le résultat final (`StartupResult` / `ShutdownResult`) expose les détails.
- **`hasattr` guards** : le service appelle des méthodes optionnelles (save_state, load_last_calibration) via introspection pour éviter de créer des interfaces supplémentaires.
