# fake_arcus_performax_4ex — Intention

## Rationale

Le pilote Arcus vivait en deux copies, ici et dans le repo Arcus-Performax-4EX,
qui divergeaient. Depuis le 2026-11-27, la source unique est le paquet `arcus_performax_4ex` (repo Arcus-Performax-4EX, github.com/Luciosmic/driver-arcus-performax-4ex),
dont AEFI dépend par `pyproject.toml` (tag git).

## Responsibility

- Garder le chemin d'import AEFI de `arcus_performax_4ex.fake.fake_arcus_performax4ex_controller` : réexporter ses noms, sans code
  propre.

## Design

- Toute correction se fait dans le repo Arcus-Performax-4EX, puis AEFI monte le tag
  dans `pyproject.toml`.
- Documentation, tests et intention complète : à côté du module, dans le paquet.
