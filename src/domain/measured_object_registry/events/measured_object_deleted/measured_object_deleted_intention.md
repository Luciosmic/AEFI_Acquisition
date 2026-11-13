---
type: evenement-de-domaine::solidai-ddd
tldr: "Fait passé : un objet mesuré a été **retiré** du registre (identité, dernier nom, date)."
code: ["[[src/domain/measured_object_registry/events/measured_object_deleted/measured_object_deleted.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/measured_object_registry/measured_object_registry_intention]]"
---
# measured_object_deleted — Intention

## Rationale

Un objet supprimé depuis le panneau « Objets mesurés » doit disparaître aussitôt
des sélecteurs des panneaux Scan, Continuous Reading et Frequency Sweep ; et le
journal d'événements doit garder ce qui a été retiré et quand, puisque le
registre, lui, ne le garde plus.

## Responsibility

- Fait passé : un objet mesuré a été **retiré** du registre (identité, dernier
  nom, date). Rejouable sans état courant (nom dénormalisé).

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- Émis par l'aggregate `MeasuredObjectRegistry.delete`.
- Topic : `"measuredobjectdeleted"`.
- Les exports déjà écrits ne changent pas : ils portent l'identité et le nom
  de l'objet en clair (`feature_of_interest`).
