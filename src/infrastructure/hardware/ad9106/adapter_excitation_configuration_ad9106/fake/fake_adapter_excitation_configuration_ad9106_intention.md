---
type: doublure-de-test::solidai-hexagonal
tldr: "Doublure `fake_adapter_excitation_configuration_ad9106` : Implémenter `IExcitationPort` en mémoire : `apply_excitation()`, `set_gain()`, `set_link_dds1_dds2()`."
code: ["[[src/infrastructure/hardware/ad9106/adapter_excitation_configuration_ad9106/fake/fake_adapter_excitation_configuration_ad9106.py]]"]
cause_de_changement: outil
implements: ["[[src/application/shared/excitation_configuration_service/ports/i_excitation_port_intention]]"]
double_de: "[[src/infrastructure/hardware/ad9106/adapter_excitation_configuration_ad9106/adapter_excitation_configuration_ad9106_intention]]"
---
# fake_adapter_excitation_configuration_ad9106 — Intention

## Rationale

Mock de `IExcitationPort` pour les tests de `ExcitationConfigurationService` sans l'AD9106.

## Responsibility

- Implémenter `IExcitationPort` en mémoire : `apply_excitation()`, `set_gain()`,
  `set_link_dds1_dds2()`.
- Enregistrer les configurations appliquées pour les assertions.

## Design

- **`infrastructure/mocks/`**.
- Spy attributes : `last_parameters` (dernier `ExcitationParameters` appliqué ou modifié par
  `set_gain()`) et `linked` (dernier état passé à `set_link_dds1_dds2()`, défaut `True`).
- `last_parameters` est aussi exposé en property `last_parameters` sur
  `AdapterExcitationConfigurationAD9106` (Real) — duck-typing partagé utilisé par
  `ExcitationAwareAcquisitionPort` pour marcher indifféremment avec le Real ou ce Mock.
