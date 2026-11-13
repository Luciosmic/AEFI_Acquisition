# i_excitation_port — Intention

## Rationale

Port outbound du `ExcitationConfigurationService` vers le hardware DDS (AD9106). Abstraire le protocole SPI/série de la logique applicative de configuration d'excitation.

## Responsibility

- `apply_excitation(params)` : appliquer mode/niveaux/fréquence.
- `set_gain(level_s1_s2, level_s3_s4)` : écrire uniquement le gain, sans publier d'event — pour
  le cycle mute/unmute transitoire des scans différentiels (ne doit pas resynchroniser le
  panel Hardware Config à chaque point de scan).
- `set_link_dds1_dds2(linked)` : persister et publier le changement du lien de gain
  DDS1/DDS2 (S1-S2 = S3-S4), partagé avec le paramètre `link_dds1_dds2` du panel Hardware
  Advanced Config.

## Design

- **Port outbound** co-localisé dans `excitation_configuration_service/`.
- Implémenté par `AdapterExcitationConfigurationAD9106` (Real) et `MockExcitationPort` (Mock,
  `infrastructure/mocks/adapter_mock_i_excitation_port.py`).
