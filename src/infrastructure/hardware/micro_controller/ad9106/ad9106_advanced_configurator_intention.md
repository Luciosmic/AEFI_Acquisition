# ad9106_advanced_configurator — Intention

## Rationale

Implémentation de `IHardwareAdvancedConfigurator` pour l'AD9106. Expose les paramètres avancés de l'AD9106 (fréquence d'horloge, interpolation, registres de mémoire de forme d'onde) dans le panneau configuration avancée.

## Responsibility

- Définir les specs des paramètres AD9106 avancés via `get_parameter_specs()`.
- Appliquer et persister les configurations.

## Design

- `hardware_id = "ad9106"`.
- Implémente `IHardwareAdvancedConfigurator`.
