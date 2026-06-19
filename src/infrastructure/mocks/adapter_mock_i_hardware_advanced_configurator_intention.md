# adapter_mock_i_hardware_advanced_configurator — Intention

## Rationale

Mock de `IHardwareAdvancedConfigurator` pour les tests de `HardwareConfigurationService` sans hardware.

## Responsibility

- Implémenter `get_parameter_specs()`, `apply_config()`, `save_config_as_default()` en mémoire.
- Retourner un jeu de specs fictif configurable pour les tests.

## Design

- **`infrastructure/mocks/`**.
- `hardware_id` et `display_name` configurables au constructeur.
