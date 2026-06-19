# adapter_mock_i_continuous_acquisition_executor — Intention

## Rationale

Mock de `IContinuousAcquisitionExecutor` pour les tests de `ContinuousAcquisitionService` sans thread ni hardware.

## Responsibility

- Implémenter `start()`, `stop()`, `update_config()` comme no-ops avec recording.
- Exposer `is_running`, `start_count`, `stop_count` pour les assertions.

## Design

- **`infrastructure/mocks/`**.
- Synchrone par design : les tests de service ne doivent pas dépendre de threads.
