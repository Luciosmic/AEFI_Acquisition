# operator — Intention

## Rationale

Sans entité opérateur, une acquisition ne connaît qu'un nom tapé à la main :
deux saisies du même opérateur donnent deux orthographes, et rien ne permet
de regrouper après coup les acquisitions d'une même personne. Un nom n'est
pas une identité : s'il est corrigé, toutes les traces passées deviennent
orphelines.

## Responsibility

- Porter l'identité stable d'un opérateur (`operator_id`), son nom tel
  qu'enregistré (espaces normalisés) et sa date d'enregistrement.

## Design

- `@dataclass(frozen=True)` ; identité = `operator_id` (UUID).
- L'unicité de l'orthographe n'est pas une règle de l'entité seule : elle
  porte sur l'ensemble des opérateurs, donc sur l'aggregate `OperatorRegistry`.
