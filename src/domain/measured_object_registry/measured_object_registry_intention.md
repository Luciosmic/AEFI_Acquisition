# measured_object_registry — Intention

## Rationale

Un champ texte libre pour l'objet mesuré le fait retaper à chaque
acquisition : « Bouteille d'eau », « bouteille d'eau », « Bouteille  d'eau » finissent
comme trois objets mesurés dans les exports, et regrouper les acquisitions d'un
même objet devient impossible. La règle « un objet mesuré, une seule
orthographe » porte sur l'ensemble des objets mesurés connus : elle ne peut vivre
ni dans un widget (contournable, pas testable seul), ni dans une entité
isolée (qui ne voit pas les autres).

Calqué sur le registre des opérateurs (`domain/operator_registry/`), même invariants.

## Responsibility

- `register(name)` : rendre l'objet mesuré de ce nom — l'existant si
  l'orthographe est déjà connue à la casse et aux espaces près (aucun
  événement), sinon un nouvel objet mesuré (`MeasuredObjectRegistered`).
- Invariants : I1 une seule orthographe ; I2 un nom non vide
  (`MeasuredObjectNameBlankError`) ; I3 identité stable (`measured_object_id` jamais réattribué).

## Design

- Aggregate root (dataclass) reconstruit depuis le dépôt (`reconstitute`),
  sans I/O ni import hors `domain/`.
- Nom enregistré = espaces normalisés (`" ".join(name.split())`) ; clé de
  comparaison = ce nom en `casefold()`.
- `register` rend `(measured_object, created)` : `created` permet au service de ne
  persister et publier que les créations.
- Événements accumulés puis vidés par `domain_events` (même patron que
  l'aggregate `Calibration`).
