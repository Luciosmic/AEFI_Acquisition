# adapter_mock_i_hardware_advanced_configurator — Intention

## Rationale

Mock de `IHardwareAdvancedConfigurator` pour les tests de `HardwareConfigurationService` sans hardware.

## Responsibility

- Implémenter `get_parameter_specs()`, `apply_config()`, `save_config_as_default()`,
  `reset_to_default()` en mémoire.
- Retourner un jeu de specs fictif configurable pour les tests.

## Design

- **`infrastructure/mocks/`**.
- `hardware_id` et `display_name` configurables au constructeur.
- **Non utilisé actuellement** : aucune classe du code ne l'instancie (vérifié par grep). Gardé
  conforme à l'ABC au cas où il serait réactivé plus tard.
