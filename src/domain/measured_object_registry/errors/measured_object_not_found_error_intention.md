---
type: atome::solidai-atome
tldr: "Nommer un seul refus métier : « l'objet mesuré à renommer ou supprimer est dans le registre »."
code: ["[[src/domain/measured_object_registry/errors/measured_object_not_found_error.py]]"]
cause_de_changement: regle-metier
---
# measured_object_not_found_error — Intention

## Rationale

Le panneau « Objets mesurés » renomme ou supprime un objet par son identité.
Si cet objet a déjà disparu du registre (supprimé entre-temps, fichier modifié
à la main), renommer ou supprimer « rien » en silence laisserait croire à
l'opérateur que son geste a porté.

## Responsibility

- Nommer un seul refus métier : « l'objet mesuré à renommer ou supprimer est
  dans le registre ».

## Design

- Sous-classe de `LookupError`.
- Levée par `MeasuredObjectRegistry.rename` et `MeasuredObjectRegistry.delete` ;
  traduite par `MeasuredObjectService` en refus du use case (`MeasuredObjectNotFound`).
- Testé via son émetteur : `measured_object_registry_test.py`.
