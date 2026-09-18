# ads131a04_advanced_configurator — Intention

## Rationale

Implémentation de `IHardwareAdvancedConfigurator` pour l'ADS131A04. Expose les paramètres configurables de l'ADC (gain, filtre, taux d'échantillonnage) dans le panneau de configuration avancée sans exposer les registres hardware.

## Responsibility

- Définir les specs des paramètres ADS131A04 avancés via `get_parameter_specs()` — lit
  uniquement `ads131a04_default_config.json` (pas de résolution default+last comme AD9106/MCU,
  angle mort connu et documenté dans `_system/ops/tasks.md`).
- Appliquer les configurations et les persister par défaut.
- `reset_to_default()` : réapplique le default (générique — `get_parameter_specs()` étant déjà
  non résolu, son `default_value` EST le vrai default, réutilisable tel quel dans
  `apply_config()`).

## Design

- `hardware_id = "ads131a04"`.
- Implémente `IHardwareAdvancedConfigurator`.
