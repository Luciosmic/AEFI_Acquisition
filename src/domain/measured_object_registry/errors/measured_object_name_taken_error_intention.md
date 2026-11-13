---
type: atome::solidai-atome
tldr: "Nommer un seul refus métier : renommer un objet mesuré vers l'orthographe d'un autre (invariant I1 du registre)."
code: ["[[src/domain/measured_object_registry/errors/measured_object_name_taken_error.py]]"]
cause_de_changement: regle-metier
---
# measured_object_name_taken_error — Intention

## Rationale

À l'enregistrement, une orthographe déjà connue rend l'objet existant : il n'y
a rien à refuser. Au renommage, il n'y a pas d'objet à rendre : renommer
« plaque » en « Bouteille d'eau » alors que « bouteille d'eau » existe ferait
deux objets d'une même orthographe, et l'invariant I1 tomberait.

## Responsibility

- Nommer un seul refus métier : renommer un objet mesuré vers l'orthographe
  d'un autre objet, à la casse et aux espaces près (invariant I1 du registre
  `MeasuredObjectRegistry`).

## Design

- Sous-classe de `ValueError`, comme les autres erreurs domaine du projet.
- Levée par `MeasuredObjectRegistry.rename` ; traduite par `MeasuredObjectService`
  en refus du use case (`MeasuredObjectNameTaken`).
- Testé via son émetteur : `measured_object_registry_test.py`.
