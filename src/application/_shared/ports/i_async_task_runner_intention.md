# i_async_task_runner — Intention

## Rationale

Les application services (`ScanApplicationService`, `ElectricFieldProbeService`) ont besoin de lancer une boucle en tâche de fond sans dépendre du mécanisme de concurrence (threading, asyncio, pool distant). Le port isole cette responsabilité d'infra derrière une interface stable.

Ce port est placé dans `application/_shared/ports/` car il est consommé par plusieurs services et sa cause de changement (choix du mécanisme de concurrence) est orthogonale à chaque use case. Cf. `standard-solidai-shared-domain-concept-extraction` appliqué au niveau application.

## Responsibility

- `IAsyncTaskRunner.submit(callable) -> TaskHandle` : soumet une callable pour exécution en tâche de fond, retour immédiat.
- `TaskHandle.is_running()` : indique si la callable est encore active.
- `TaskHandle.wait(timeout)` : bloque jusqu'à la fin de la callable ou expiration du timeout.

## Design

- Fire-and-forget. La callable est autonome : elle capture ses dépendances via closure et rapporte son résultat via le bus d'events domain ou des mutations d'agrégat.
- **Aucune sémantique d'annulation** dans le port : l'annulation est un concept application (l'agrégat `StepScan.cancel()` ou un `threading.Event` de stream possédé par le service). Introduire `cancel()` dans le port ferait fuiter des concepts infra (thread interrupt, `Future.cancel`).
- Le runner ne wrappe pas la callable dans un try/except — les erreurs programmeur restent visibles.
- L'implémentation par défaut (`ThreadPoolTaskRunner`) utilise `threading.Thread(daemon=True)` ; un Fake synchrone existe pour les tests.
