# adapter_i_acquisition_port_ads131a04 — Intention

## Rationale

Adaptateur Real implémentant `IAcquisitionPort` pour l'ADC ADS131A04 via le MCU. C'est l'unique point de liaison entre l'abstraction d'acquisition domain et le hardware ADC réel — un échantillon synchrone 6-canaux par appel.

## Responsibility

- Implémenter `acquire_sample() → VoltageMeasurement` : déclencher une acquisition ADS131A04, lire les 6 canaux (X/Y/Z × In-Phase/Quadrature), convertir en volts, retourner.
- Gérer les erreurs de communication MCU et les convertir en exceptions Python claires.

## Design

- Dépend de `ADS131Controller` pour les commandes ADC.
- La conversion ADC → volts (facteur de gain, référence) est encapsulée ici, pas dans le domain.
