# ads131_controller — Intention

## Rationale

Controller bas-niveau de l'ADS131A04 (ADC 24-bit 4 canaux de Texas Instruments) via le MCU. Gère les commandes de configuration et de lecture spécifiques au registre ADS131A04, en dessous de la couche adaptateur.

## Responsibility

- Configurer les registres de l'ADS131A04 (gain, mode, filtres).
- Déclencher et lire une conversion ADC synchrone via le MCU.
- Interpréter les trames de données brutes de l'ADS131A04.

## Design

- **Couche hardware-specific** : connaît le jeu de registres ADS131A04 (datasheet TI).
- Utilisé par les adaptateurs `adapter_i_acquistion_port_ads131a04` et `adapter_i_continuous_acquisition_ads131a04`.
