---
type: evenement-de-domaine::solidai-ddd
tldr: "Événement `motion_conversion_changed` : Annoncer qu'une conversion mm/impulsion déjà appliquée a été remplacée : ancienne et nouvelle valeur (µm/impulsion), moteur et driver concernés."
code: ["[[src/domain/shared_kernel/events/motion_conversion_changed/motion_conversion_changed.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/shared_kernel/operation_result_intention]]"
---
# motion_conversion_changed — Intention

## Rationale

Une recalibration (nouvelle entrée de transmission mécanique) doit s'appliquer sans
redémarrage (décision du 2026-10-15). `MotionConversionBecameAvailable` dit « le banc
peut bouger désormais » : il ne dit pas qu'une échelle déjà en service vient d'être
remplacée. Sans événement distinct, l'historique ne permettrait pas de savoir à partir
de quand les positions en mm d'une session ont changé d'échelle.

## Responsibility

- Annoncer qu'une conversion mm/impulsion déjà appliquée a été remplacée : ancienne et
  nouvelle valeur (µm/impulsion), moteur et driver concernés.

## Design

- Publié par `MotionConversionHandler`, jamais pendant un scan (le changement est alors
  différé à sa fin).
- Topic : `motionconversionchanged`. Valeurs en µm par impulsion (unité dans le nom).
