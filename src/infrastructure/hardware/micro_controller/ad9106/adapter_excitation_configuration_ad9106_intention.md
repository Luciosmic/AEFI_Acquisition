# adapter_excitation_configuration_ad9106 — Intention

## Rationale

Adaptateur Real implémentant `IExcitationPort` pour l'AD9106 DDS. Traduit les `ExcitationParameters` domain en commandes de registres AD9106 concrètes.

## Responsibility

- Implémenter `IExcitationPort` : appliquer fréquence, amplitude, mode, phase sur l'AD9106.
- Convertir les valeurs domain (Hz, V) en valeurs de registres hardware (DAC counts, frequency tuning words).

## Design

- Dépend de `AD9106Controller` pour les appels registres.
- Les formules de conversion (FTW, amplitude DAC) sont encapsulées ici.
