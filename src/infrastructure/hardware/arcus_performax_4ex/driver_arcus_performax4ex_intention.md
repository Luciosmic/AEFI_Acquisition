---
type: atome::solidai-atome
tldr: "Réexporte le pilote bas niveau Arcus Performax 4EX du paquet arcus_performax_4ex."
code: ["[[src/infrastructure/hardware/arcus_performax_4ex/adapter_arcus_speed_config.py]]", "[[src/infrastructure/hardware/arcus_performax_4ex/adapter_lifecycle_arcus_performax4ex/adapter_lifecycle_arcus_performax4ex.py]]", "[[src/infrastructure/hardware/arcus_performax_4ex/adapter_motion_port_arcus_performax4ex/adapter_motion_port_arcus_performax4ex.py]]", "[[src/infrastructure/hardware/arcus_performax_4ex/arcus_advanced_configuration/arcus_advanced_configuration.py]]", "[[src/infrastructure/hardware/arcus_performax_4ex/composition_root_arcus.py]]", "[[src/infrastructure/hardware/arcus_performax_4ex/driver_arcus_performax4ex.py]]"]
cause_de_changement: outil
---
# driver_arcus_performax4ex — Intention

## Rationale

Le pilote Arcus vivait en deux copies, ici et dans le repo Arcus-Performax-4EX,
qui divergeaient. Depuis le 2026-11-27, la source unique est le paquet `arcus_performax_4ex` (repo Arcus-Performax-4EX, github.com/Luciosmic/driver-arcus-performax-4ex),
dont AEFI dépend par `pyproject.toml` (tag git).

## Responsibility

- Garder le chemin d'import AEFI de `arcus_performax_4ex.driver_arcus_performax4ex` : réexporter ses noms, sans code
  propre.

## Design

- Toute correction se fait dans le repo Arcus-Performax-4EX, puis AEFI monte le tag
  dans `pyproject.toml`.
- Documentation, tests et intention complète : à côté du module, dans le paquet.
