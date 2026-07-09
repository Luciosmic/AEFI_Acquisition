# i_hardware_advanced_configurator — Intention

## Rationale

Définir le contrat que chaque périphérique hardware avancé (Arcus, MCU, AD9106, ADS131A04) doit respecter pour être configurable depuis le `HardwareConfigurationService`. Permet au service d'agréger des configurateurs hétérogènes via un type commun.

## Responsibility

- Déclarer les propriétés `hardware_id: str` et `display_name: str` pour l'identification.
- Déclarer `get_parameter_specs() → List[HardwareAdvancedParameterSchema]` (méthode de classe).
- Déclarer `apply_config(config: Dict[str, Any])` et `save_config_as_default(config: Dict[str, Any])`.

## Design

- **ABC** avec `@abstractmethod` exclusivement.
- `hardware_id` sert de clé dans le dictionnaire du `HardwareConfigurationService`.
- `get_parameter_specs()` est une méthode de classe statique : le service l'appelle via `type(provider).get_parameter_specs()` pour obtenir le schéma indépendamment de l'état de l'instance.
