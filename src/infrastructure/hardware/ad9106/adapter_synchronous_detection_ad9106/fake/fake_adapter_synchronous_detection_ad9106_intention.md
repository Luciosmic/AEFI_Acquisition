# fake_adapter_synchronous_detection_ad9106 — Intention

## Rationale

Le service de détection synchrone lit et écrit des registres de phase de l'AD9106 par `ISynchronousDetectionHardwarePort`. Sans double en mémoire, chaque test du service demanderait la puce et sa liaison série, et la restauration de la configuration manuelle ne pourrait pas se rejouer.

## Responsibility

- Tenir `ISynchronousDetectionHardwarePort` entièrement en mémoire : les registres de phase, le gain de verrouillage et l'application de la quadrature.
- Rejouer la persistance manuelle : `set_ch3_phase_register(value, persist=True)` fixe la base que `restore_manual_configuration()` recharge ; sans base enregistrée, la restauration ne change rien.

## Design

- La classe `MockSynchronousDetectionHardwarePort` garde son nom : de nombreux tests l'importent.
- Aucune entrée-sortie : un dictionnaire de registres, des compteurs d'appels (`restore_manual_configuration_calls`) et les gains.
- Piste de réel : l'adaptateur `adapter_synchronous_detection_ad9106` du même appareil. Remplace l'ancien `infrastructure/mocks/adapter_mock_i_synchronous_detection_hardware_port.py` (sans intention).
