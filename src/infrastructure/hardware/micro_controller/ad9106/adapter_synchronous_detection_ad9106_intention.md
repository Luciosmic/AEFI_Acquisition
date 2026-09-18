# adapter_synchronous_detection_ad9106 — Intention

## Rationale

Adaptateur Real implémentant `ISynchronousDetectionHardwarePort` pour l'AD9106 DDS. ch3/ch4
sont les canaux dédiés à la référence de démodulation de la détection synchrone (ch1/ch2
restent le port de l'excitation, voir `AdapterExcitationConfigurationAD9106`). Ne crée aucune
nouvelle connexion série : reçoit le `AD9106Controller` et le `AD9106AdvancedConfigurator` déjà
instanciés et partagés par `MCUCompositionRoot`.

## Responsibility

- Implémenter `ISynchronousDetectionHardwarePort` :
  - `get_all_channel_phase_registers()` : snapshot des registres de phase des 4 canaux DDS,
    lu depuis l'état mémoire logiciel du controller (`AD9106Controller.get_memory_state()`) —
    pas une relecture matérielle réelle (limitation assumée, documentée dans le port domain).
  - `set_ch3_phase_register(value)` : écrit le registre de phase du canal 3 en passant par
    l'écrivain unique `AD9106AdvancedConfigurator.apply_config({"ch3_phase": value})` — jamais
    d'appel direct au controller, pour que l'enforcement quadrature ch3/ch4 et la persistance
    `ad9106_last_config.json` restent centralisés dans le configurator.
  - `is_quadrature_enforcement_enabled()` : délègue à
    `AD9106AdvancedConfigurator.is_dds3_dds4_quadrature_enforced()`, lecture seule du flag
    hardware config `enforce_dds3_dds4_quadrature`.

## Design

- Dépend de `AD9106Controller` et `AD9106AdvancedConfigurator`, tous deux partagés (mêmes
  instances que `AdapterExcitationConfigurationAD9106`/`MCUCompositionRoot`) — aucune nouvelle
  connexion série, aucun nouvel état.
- Adaptateur volontairement fin (pure délégation) : toute la logique de résolution config et
  d'enforcement quadrature vit déjà dans `AD9106AdvancedConfigurator`.
