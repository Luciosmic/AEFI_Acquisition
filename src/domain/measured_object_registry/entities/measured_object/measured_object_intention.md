---
type: entite::solidai-ddd
tldr: "Porter l'identité stable d'un objet mesuré (measured_object_id), son nom tel qu'enregistré (espaces normalisés) et sa date d'enregistrement."
code: ["[[src/domain/measured_object_registry/entities/measured_object/measured_object.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/measured_object_registry/measured_object_registry_intention]]"
---
# measured_object — Intention

## Rationale

Sans entité objet mesuré, une acquisition ne connaît qu'un nom tapé à la main :
deux saisies du même objet donnent deux orthographes, et rien ne permet
de regrouper après coup les acquisitions d'un même objet. Un nom n'est
pas une identité : s'il est corrigé, toutes les traces passées deviennent
orphelines.

## Responsibility

- Porter l'identité stable d'un objet mesuré (`measured_object_id`), son nom tel
  qu'enregistré (espaces normalisés) et sa date d'enregistrement.

## Design

- `@dataclass(frozen=True)` ; identité = `measured_object_id` (UUID).
- L'unicité de l'orthographe n'est pas une règle de l'entité seule : elle
  porte sur l'ensemble des objets mesurés, donc sur l'aggregate `MeasuredObjectRegistry`.
