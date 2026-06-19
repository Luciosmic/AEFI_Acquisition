# ADS131A04 — Adaptateur ADC

## Rationale
Ce module implémente l'acquisition des tensions électriques mesurées par le capteur AEFI via l'ADC Texas Instruments ADS131A04. Il traduit les concepts domaine (incertitude de mesure) en paramètres hardware (gain PGA, OSR, fréquence d'échantillonnage).

## Responsibility
- `ADS131Controller` (`ads131_controller.py`) : contrôleur bas-niveau. Configure les registres de l'ADC (ICLK divider, OSR, gains par canal) via `MCU_SerialCommunicator` et déclenche les acquisitions.
- `ADS131A04Adapter` (`adapter_i_acquistion_port_ads131a04.py`) : implémenter `IAcquisitionPort`. Traduit `MeasurementUncertainty` → `ADCHardwareConfig` (gain, OSR, Vref), lit les données brutes et les convertit en `VoltageMeasurement` avec le mapping de canaux domaine (voltage_x_in_phase = ADC1_Ch1, etc.).

## Design
- La formule d'incertitude matérielle guide le choix du gain et de l'OSR : `Incertitude ≈ Vref / (2^N · Gain · √OSR)`.
- Le mapping canal hardware → composante domaine est centralisé dans l'adaptateur pour préserver la pureté du domaine.
- L'ADC supporte 16 valeurs d'OSR (de 32 à 4096) et 8 niveaux de gain PGA (1 à 128) définis par le datasheet ADS131A04.
