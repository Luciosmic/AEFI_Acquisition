---
type: value-object::solidai-ddd
tldr: "La rotation du capteur qu'une acquisition a réellement appliquée : trois angles en degrés et la convention dans laquelle ils sont écrits, tels que le fichier des paramètres les donne."
code: ["[[external_modules/aefi_post_processor_module/domain/acquisition_record/value_objects/applied_rotation/applied_rotation.py]]"]
cause_de_changement: regle-metier
part_of: "[[external_modules/aefi_post_processor_module/domain/acquisition_record/acquisition_record_intention]]"
---
# applied_rotation — Intention

## Rationale

L'acquisition traite en fin de scan avec les angles de la calibration active (pour la bouteille d'eau du 13 novembre : 34,9°, 45,7°, −5,3°). Le retraitement par lot prenait les angles idéaux du gabarit (35,3°, 45°, 0°) : le même scan donnait deux « repères tournés » selon le chemin. Sans valeur qui porte les angles appliqués, le post-traitement ne pouvait que deviner, et un triplet d'angles sans sa convention se lit dans le mauvais sens sans qu'on le voie.

## Responsibility

- Porter les trois angles (θx, θy, θz) en degrés de la rotation de montage que l'acquisition a appliquée, et la convention (type, ordre, sens) dans laquelle ils sont écrits.
- Porter l'origine des angles (calibrés, gabarit idéal) et l'identifiant de la calibration quand le fichier les dit.
- Refuser un triplet qui n'a pas trois nombres finis.

## Design

- Une `@dataclass(frozen=True)`, sur la bibliothèque standard seule. La convention reste trois chaînes : le domaine ne connaît pas `RotationConvention` de l'acquisition ; c'est le traducteur de l'infrastructure qui l'emprunte et refuse une convention que l'application ne sait pas appliquer. Une `AppliedRotation` n'existe donc que pour une convention prise en charge.
- Les angles sont un tuple, comparable et utilisable tel quel par le calcul de rotation de repère.
