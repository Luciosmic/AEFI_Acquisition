# hardware_advanced_parameter_schema — Intention

## Rationale

Value object décrivant la spécification d'un paramètre hardware configurable (nom, type, valeur par défaut, plage, unité). Permet à la UI (`HardwareAdvancedConfigPanel`) de générer dynamiquement les champs de configuration sans connaître les détails de chaque périphérique.

## Responsibility

- Stocker : `name: str`, `type: str` (int/float/bool/select), `default`, `min`, `max`, `options`, `unit`, `description`.
- Servir de schéma retourné par `IHardwareAdvancedConfigurator.get_parameter_specs()`.

## Design

- **`@dataclass(frozen=True)`** : le schéma d'un paramètre est une métadonnée stable.
- La UI itère sur `List[HardwareAdvancedParameterSchema]` pour construire les widgets de configuration dynamiquement.
