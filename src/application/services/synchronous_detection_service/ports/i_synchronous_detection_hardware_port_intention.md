# i_synchronous_detection_hardware_port — Intention

## Rationale

Port outbound du `SynchronousDetectionService` vers le hardware DDS (AD9106). Abstrait le protocole SPI/série pour les canaux ch3/ch4 (référence de démodulation de la détection synchrone), séparé de `IExcitationPort` qui pilote ch1/ch2 (excitation).

## Responsibility

- `get_all_channel_phase_registers()` : snapshot mémoire logicielle des 4 registres de phase (ch1-4) — pas de lecture matérielle réelle, limitation assumée et documentée.
- `set_ch3_phase_register(value)` : écrit uniquement le registre de phase ch3, via l'écrivain unique `AD9106AdvancedConfigurator.apply_config`.
- `is_quadrature_enforcement_enabled()` : lecture seule du flag hardware config `enforce_dds3_dds4_quadrature` — pas de commande de toggle ici (l'enforcement est un invariant électronique, pas une décision applicative de ce service).

## Design

- **Port outbound** co-localisé dans `synchronous_detection_service/`.
- Implémenté par `AdapterSynchronousDetectionAD9106` (Real, infrastructure) et `MockSynchronousDetectionHardwarePort` (Fake, `infrastructure/mocks/adapter_mock_i_synchronous_detection_hardware_port.py`).
