---
type: doublure-de-test::solidai-hexagonal
tldr: "Réexporte le port simulé en incréments bruts du paquet arcus_performax_4ex (temps de l'horloge injectée, capteur d'origine à 7 incréments, requête de 44 ms)."
code: ["[[src/infrastructure/hardware/arcus_performax_4ex/adapter_raw_increment_motion_arcus/fake/fake_adapter_raw_increment_motion_arcus.py]]"]
cause_de_changement: outil
implements: ["[[src/application/test_bench_calibration/raw_increment_motion/ports/i_raw_increment_motion_port_intention]]"]
double_de: "[[src/infrastructure/hardware/arcus_performax_4ex/adapter_raw_increment_motion_arcus/adapter_raw_increment_motion_arcus_intention]]"
---
# fake_adapter_raw_increment_motion_arcus — Intention

## Rationale

Le pilote Arcus vivait en deux copies, ici et dans le repo Arcus-Performax-4EX,
qui divergeaient. Depuis le 2026-11-27, la source unique est le paquet `arcus_performax_4ex` (repo Arcus-Performax-4EX, github.com/Luciosmic/driver-arcus-performax-4ex),
dont AEFI dépend par `pyproject.toml` (tag git).

## Responsibility

- Garder le chemin d'import AEFI de `arcus_performax_4ex.fake.fake_raw_increment_motion_port` : réexporter ses noms, sans code
  propre.

## Design

- Toute correction se fait dans le repo Arcus-Performax-4EX, puis AEFI monte le tag
  dans `pyproject.toml`.
- Documentation, tests et intention complète : à côté du module, dans le paquet.
