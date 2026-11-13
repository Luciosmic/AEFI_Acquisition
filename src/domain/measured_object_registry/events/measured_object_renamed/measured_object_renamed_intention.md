---
type: evenement-de-domaine::solidai-ddd
tldr: "Fait passé : un objet mesuré du registre a changé de nom (identité, ancien nom, nouveau nom, date)."
code: ["[[src/domain/measured_object_registry/events/measured_object_renamed/measured_object_renamed.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/measured_object_registry/measured_object_registry_intention]]"
---
# measured_object_renamed — Intention

## Rationale

Un objet nommé trop vite (« hexagone_metallique » pour un cylindre à base
hexagonale) se corrige sans changer d'identité : les acquisitions passées
gardent la même `measured_object_id`. Les sélecteurs doivent montrer le nouveau
nom aussitôt, et le journal doit garder l'ancien, pour relier les exports
écrits avant le renommage.

## Responsibility

- Fait passé : un objet mesuré du registre a changé de nom (identité, ancien
  nom, nouveau nom, date). Rejouable sans état courant.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- Émis par l'aggregate `MeasuredObjectRegistry.rename`, seulement si le nom
  enregistré change : la même orthographe ne produit rien (un log, pas un
  événement).
- Topic : `"measuredobjectrenamed"`.
- Les exports déjà écrits ne changent pas : ils gardent le nom saisi au démarrage.
