# ads131a04_advanced_configurator — Intention

## Rationale

Implémentation de `IHardwareAdvancedConfigurator` pour l'ADS131A04. Expose les paramètres configurables de l'ADC (gain, filtre, taux d'échantillonnage) dans le panneau de configuration avancée sans exposer les registres hardware.

## Responsibility

- Définir les specs des paramètres ADS131A04 avancés via `get_parameter_specs()` — lit
  uniquement `ads131a04_default_config.json` (pas de résolution default+last comme AD9106/MCU,
  angle mort connu et documenté dans `_system/ops/tasks.md`).
- **Écrivain unique de la config ADC** : `apply_persisted_config(adc_config, persist)` écrit tout
  (diviseurs, OSR, référence, gains) au chip via `ADS131Controller` ET charge la même config dans
  `ADS131A04Adapter` (conversion counts→V). Appelé par l'Apply du panel (`apply_config`, forme
  plate UI, `persist=True`) et par `MCULifecycleAdapter` au boot (`persist=False` : sinon chaque
  boot recopierait le default dans `last_config`, qui masquerait ensuite toute édition du
  default). Sans écrivain unique, le chip et la conversion peuvent diverger silencieusement
  (Vref, bit réservé, OSR — divergences constatées 2026-09-25).
- Un seul nom par grandeur, identique en clé UI et en clé JSON : `negative_charge_pump`,
  `high_resolution`, `reference_voltage` (V), `reference_source` (`Internal`/`External`),
  `oversampling_ratio`, `clkin_divider`, `iclk_divider`, `channels.N.gain`.
- `reset_to_default()` : réapplique le default (générique — `get_parameter_specs()` étant déjà
  non résolu, son `default_value` EST le vrai default, réutilisable tel quel dans
  `apply_config()`).

## Design

- `hardware_id = "ads131a04"`.
- Implémente `IHardwareAdvancedConfigurator`.
