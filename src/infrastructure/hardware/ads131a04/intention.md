# ADS131A04 — Adaptateur ADC

## Rationale
Ce module implémente l'acquisition des tensions électriques mesurées par le capteur AEFI via l'ADC Texas Instruments ADS131A04. Il traduit les concepts domaine (incertitude de mesure) en paramètres hardware (gain numérique, OSR, fréquence d'échantillonnage).

## Responsibility
- `ADS131Controller` (`ads131_controller.py`) : contrôleur bas-niveau. Configure les registres de l'ADC (ICLK divider, OSR, gains par canal) via `MCU_SerialCommunicator` et déclenche les acquisitions.
- `ADS131A04Adapter` (`adapter_i_acquistion_port_ads131a04.py`) : implémenter `IAcquisitionPort`. Traduit `MeasurementUncertainty` → `ADCHardwareConfig` (gain, OSR, Vref), lit les données brutes et les convertit en `AefiVoltageMeasurement` avec le mapping de canaux domaine (voltage_x_in_phase = ADC1_Ch1, etc.).

## Design
- Le bruit ramené à l'entrée est fixé par l'OSR, pas par le gain (datasheet SBAS590E, §8.1, tableaux 1 à 4) : au gain 1 et Vref 2,442 V, 1,82 µVrms à OSR 4096 et 96,82 µVrms à OSR 32. À OSR donné, il change peu du gain 1 au gain 16.
- Le gain de l'ADS131A04 est un gain numérique (§9.6.2, registres ADCx 11h à 14h, « digital scaling ») : il divise la pleine échelle (±Vref/Gain) et ôte environ 6 dB de dynamique par doublement, sans réduire le bruit. Le gain utile se met en début de chaîne de mesure, sur la carte de détection.
- `estimate_uncertainty()` ne calcule que la composante de quantification, `Vref / (2^N · Gain · √OSR)`. Elle ne lit pas encore le bruit des tableaux de la datasheet, qui domine.
- Le mapping canal hardware → composante domaine est centralisé dans l'adaptateur pour préserver la pureté du domaine.
- L'ADC supporte 16 valeurs d'OSR (de 32 à 4096) et 5 niveaux de gain numérique (1, 2, 4, 8, 16), définis par le datasheet ADS131A04.
