# adapter_mock_i_aefi_acquisition_executor — Intention

## Rationale

Mock de `IAefiAcquisitionExecutor` pour les tests de `AefiAcquisitionService` sans thread ni hardware.

## Responsibility

- Implémenter `start()`, `stop()` avec un thread de simulation à cadence fixe
  réaliste (`_SIMULATION_INTERVAL_S` = 1kHz, non configurable — l'acquisition
  réelle est best-effort, mais ce mock a besoin d'un frein puisque son
  `acquire_sample()` est quasi instantané ; 1kHz reste assez rapide pour ne
  pas pénaliser les scans avec fort moyennage).
- Exposer `is_running`, `start_count`, `stop_count` pour les assertions.

## Design

- **`infrastructure/mocks/`**.
- Synchrone par design : les tests de service ne doivent pas dépendre de threads.
