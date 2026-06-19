# ads131a04_advanced_configurator — Intention

## Rationale

Implémentation de `IHardwareAdvancedConfigurator` pour l'ADS131A04. Expose les paramètres configurables de l'ADC (gain, filtre, taux d'échantillonnage) dans le panneau de configuration avancée sans exposer les registres hardware.

## Responsibility

- Définir les specs des paramètres ADS131A04 avancés via `get_parameter_specs()`.
- Appliquer les configurations et les persister par défaut.

## Design

- `hardware_id = "ads131a04"`.
- Implémente `IHardwareAdvancedConfigurator`.
