---
type: point-de-composition::solidai-hexagonal
tldr: "Point de composition `composition_root_arcus` : Instancier `DriverArcusPerformax4EX`, `AdapterMotionPortArcusPerformax4EX`, `AdapterLifecycleArcusPerformax4EX`."
code: ["[[src/infrastructure/hardware/arcus_performax_4ex/composition_root_arcus.py]]"]
cause_de_changement: outil
cable:
  - "[[src/infrastructure/hardware/arcus_performax_4ex/adapter_lifecycle_arcus_performax4ex/adapter_lifecycle_arcus_performax4ex_intention]]"
  - "[[src/infrastructure/hardware/arcus_performax_4ex/adapter_motion_port_arcus_performax4ex/adapter_motion_port_arcus_performax4ex_intention]]"
  - "[[src/infrastructure/hardware/arcus_performax_4ex/adapter_raw_increment_motion_arcus/adapter_raw_increment_motion_arcus_intention]]"
  - "[[src/infrastructure/hardware/arcus_performax_4ex/arcus_advanced_configuration/arcus_advanced_configuration_intention]]"
---
# composition_root_arcus — Intention

## Rationale

Point de composition des dépendances pour le sous-système Arcus. Instancie le driver, les adaptateurs motion et lifecycle, et les assemble pour être injectés dans le composition root global. Centraliser cette construction évite la duplication dans les tests et les scripts.

## Responsibility

- Instancier `DriverArcusPerformax4EX`, `AdapterMotionPortArcusPerformax4EX`, `AdapterLifecycleArcusPerformax4EX`.
- Retourner les adaptateurs prêts à l'injection dans les services applicatifs.

## Design

- **Module de composition** (pas une classe) : fonctions ou dataclass de résultat.
- Utilisé depuis le composition root global de l'application (`main.py`).
