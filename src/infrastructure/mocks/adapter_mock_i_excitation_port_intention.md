# adapter_mock_i_excitation_port — Intention

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
