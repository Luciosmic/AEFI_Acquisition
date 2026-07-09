# i_excitation_port — Intention

## Rationale

Port outbound du `ExcitationConfigurationService` vers le hardware DDS (AD9106). Abstraire le protocole SPI/série de la logique applicative de configuration d'excitation.

## Responsibility

- Déclarer les méthodes d'application des paramètres d'excitation (fréquence, amplitude, mode, activation/désactivation).

## Design

- **Port outbound** co-localisé dans `excitation_configuration_service/`.
- Implémenté par `AdapterExcitationConfigurationAD9106` (Real) et `AdapterMockIExcitationPort` (Mock).
