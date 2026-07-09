# continuous_acquisition_executor — Intention

## Rationale

Implémentation concrète de `IContinuousAcquisitionExecutor` qui gère le streaming d'acquisition en boucle continue à taux fixe (timer ou thread). Séparé de `StepScanExecutor` car la logique temporelle est différente : ici c'est un polling à fréquence fixe, pas une synchronisation event-based.

## Responsibility

- Démarrer une boucle d'acquisition à `sample_rate_hz` dans un thread séparé.
- Appeler `IAcquisitionPort.acquire_sample()` à chaque tick et publier/callback le résultat.
- Permettre la mise à jour des paramètres en cours d'exécution (`update_config`).
- Arrêter proprement la boucle sur `stop()`.

## Design

- **Thread daemon + flag d'arrêt** : stopper proprement sans join bloquant.
- **Config mutable thread-safe** : `update_config()` protégé par lock si la fréquence change en cours d'exécution.
