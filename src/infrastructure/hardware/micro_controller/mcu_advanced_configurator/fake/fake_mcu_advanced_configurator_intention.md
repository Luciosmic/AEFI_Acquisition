---
type: doublure-de-test::solidai-hexagonal
tldr: "Doublure `fake_mcu_advanced_configurator` : Implémenter `get_parameter_specs()`, `apply_config()`, `save_config_as_default()`, `reset_to_default()` en mémoire."
code: ["[[src/infrastructure/hardware/micro_controller/mcu_advanced_configurator/fake/fake_mcu_advanced_configurator.py]]"]
cause_de_changement: outil
implements: ["[[src/application/shared/hardware_configuration_service/ports/i_hardware_advanced_configurator_intention]]"]
double_de: "[[src/infrastructure/hardware/micro_controller/mcu_advanced_configurator/mcu_advanced_configurator_intention]]"
---
# fake_mcu_advanced_configurator — Intention

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
