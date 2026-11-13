---
type: atome::solidai-atome
tldr: "DTO `measured_object_dto` : `MeasuredObjectDTO` : identifiant (texte) et nom d'un objet mesuré."
code: ["[[src/application/measured_object_registry/measured_object_service/dtos/measured_object_dto.py]]"]
cause_de_changement: orchestration
---
# measured_object_dto — Intention

## Rationale

Les panneaux ne doivent pas importer l'entité domaine `MeasuredObject` (UUID,
datetime). Et l'interface doit savoir si le nom saisi existait déjà, pour
le dire à l'opérateur (« déjà enregistré : Bouteille d'eau ») plutôt que de
sélectionner silencieusement une autre orthographe que celle tapée.

## Responsibility

- `MeasuredObjectDTO` : identifiant (texte) et nom d'un objet mesuré.
- `MeasuredObjectRegistrationDTO` : l'objet mesuré à utiliser + `already_registered`.

## Design

- `@dataclass(frozen=True)`, primitives uniquement.
