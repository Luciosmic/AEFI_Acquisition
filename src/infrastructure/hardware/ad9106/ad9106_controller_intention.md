# ad9106_controller — Intention

## Rationale

Controller bas-niveau de l'AD9106 (générateur de forme d'onde DDS de Analog Devices) via le MCU. Gère les registres SPI de l'AD9106 pour programmer les sorties DDS (fréquence, amplitude, pattern de forme d'onde).

## Responsibility

- Configurer les registres AD9106 via le MCU (mode SPI bridgé).
- Programmer les patterns de forme d'onde dans la RAM interne de l'AD9106.
- Activer/désactiver les sorties.

## Design

- **Couche hardware-specific** : connaît le jeu de registres AD9106 (datasheet Analog Devices).
- Utilisé par `AdapterExcitationConfigurationAD9106` et `AD9106AdvancedConfigurator`.
