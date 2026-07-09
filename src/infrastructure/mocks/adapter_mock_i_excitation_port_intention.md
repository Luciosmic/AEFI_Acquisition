# adapter_mock_i_excitation_port — Intention

## Rationale

Mock de `IExcitationPort` pour les tests de `ExcitationConfigurationService` sans l'AD9106.

## Responsibility

- Implémenter `IExcitationPort` en mémoire.
- Enregistrer les configurations appliquées pour les assertions.

## Design

- **`infrastructure/mocks/`**.
- Spy attribute : `last_config_applied` pour vérifier les configurations dans les tests.
