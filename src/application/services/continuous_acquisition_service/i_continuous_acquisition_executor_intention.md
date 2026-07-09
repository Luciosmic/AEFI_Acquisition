# i_continuous_acquisition_executor — Intention

## Rationale

Abstraire la mécanique d'exécution de l'acquisition continue (threads, timers, callbacks) derrière un port pour que `ContinuousAcquisitionService` reste stateless et testable.

## Responsibility

- Déclarer `start(config: ContinuousAcquisitionConfig, acquisition_port: IAcquisitionPort)`.
- Déclarer `stop()`.
- Déclarer `update_config(config: ContinuousAcquisitionConfig)` pour la mise à jour à chaud.
- Déclarer `ContinuousAcquisitionConfig` comme dataclass co-localisée dans ce fichier.

## Design

- **Port outbound** dans `continuous_acquisition_service/`.
- `ContinuousAcquisitionConfig` est défini dans ce même fichier pour éviter une prolifération de modules DTOs pour un type simple.
- Implémenté par `ContinuousAcquisitionExecutor` dans `infrastructure/execution/`.
