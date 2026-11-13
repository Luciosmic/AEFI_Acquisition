# operator_dto — Intention

## Rationale

Les panneaux ne doivent pas importer l'entité domaine `Operator` (UUID,
datetime). Et l'interface doit savoir si le nom saisi existait déjà, pour
le dire à l'opérateur (« déjà enregistré : Luis Saluden ») plutôt que de
sélectionner silencieusement une autre orthographe que celle tapée.

## Responsibility

- `OperatorDTO` : identifiant (texte) et nom d'un opérateur.
- `OperatorRegistrationDTO` : l'opérateur à utiliser + `already_registered`.

## Design

- `@dataclass(frozen=True)`, primitives uniquement.
