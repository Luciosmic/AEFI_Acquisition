# arcus_advanced_configuration — Intention

## Rationale

Implémentation de `IHardwareAdvancedConfigurator` pour le contrôleur Arcus. Permet à l'utilisateur de modifier les paramètres avancés (vitesse, accélération, courant moteur) depuis le panneau de configuration avancée sans connaître les registres Arcus.

## Responsibility

- Définir les specs des paramètres Arcus avancés (`get_parameter_specs() → List[HardwareAdvancedParameterSchema]`).
- Appliquer les configurations reçues (`apply_config`).
- Persister les configurations par défaut (`save_config_as_default`).
- `reset_to_default()` : réapplique le default (générique — `get_parameter_specs()` étant déjà
  non résolu, son `default_value` EST le vrai default, réutilisable tel quel dans
  `apply_config()`).

## Design

- Implémente `IHardwareAdvancedConfigurator`.
- `hardware_id = "arcus_performax_4ex_advanced"` — clé dans le dictionnaire du `HardwareConfigurationService`.
