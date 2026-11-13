---
type: port::solidai-hexagonal
tldr: "Port sortant `i_aefi_acquisition_executor` : Déclarer `start(config: AefiAcquisitionConfig, acquisition_port: IAcquisitionPort)`."
sens: sortant
code: "[[src/application/shared/aefi_acquisition_service/ports/i_aefi_acquisition_executor.py]]"
---
# i_aefi_acquisition_executor — Intention

## Rationale

Abstraire la mécanique d'exécution de l'acquisition continue (threads, timers, callbacks) derrière un port pour que `AefiAcquisitionService` reste stateless et testable.

## Responsibility

- Déclarer `start(config: AefiAcquisitionConfig, acquisition_port: IAcquisitionPort)`.
- Déclarer `stop()`.
- Déclarer `AefiAcquisitionConfig` comme dataclass co-localisée dans ce fichier.

## Design

- **Port outbound** dans `aefi_acquisition_service/`.
- `AefiAcquisitionConfig` est défini dans ce même fichier pour éviter une prolifération de modules DTOs pour un type simple.
- Implémenté par `AefiAcquisitionExecutor` dans `infrastructure/execution/`.
