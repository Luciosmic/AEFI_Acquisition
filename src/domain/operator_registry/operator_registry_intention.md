# operator_registry — Intention

## Rationale

Un champ texte libre pour l'opérateur laisse chacun retaper son nom à chaque
acquisition : « Luis Saluden », « luis saluden », « Luis  Saluden » finissent
comme trois opérateurs dans les exports, et regrouper les acquisitions d'une
même personne devient impossible. La règle « un opérateur, une seule
orthographe » porte sur l'ensemble des opérateurs connus : elle ne peut vivre
ni dans un widget (contournable, pas testable seul), ni dans une entité
isolée (qui ne voit pas les autres).

FA : `_system/thoughts_interface/fa_operator_traceability.md` (mono-atomique,
N = 1) ; Promise Model : `_system/promise_model/operator_registry.md`.

## Responsibility

- `register(name)` : rendre l'opérateur de ce nom — l'existant si
  l'orthographe est déjà connue à la casse et aux espaces près (aucun
  événement), sinon un nouvel opérateur (`OperatorRegistered`).
- Invariants : I1 une seule orthographe ; I2 un nom non vide
  (`OperatorNameBlankError`) ; I3 identité stable (`operator_id` jamais réattribué).

## Design

- Aggregate root (dataclass) reconstruit depuis le dépôt (`reconstitute`),
  sans I/O ni import hors `domain/`.
- Nom enregistré = espaces normalisés (`" ".join(name.split())`) ; clé de
  comparaison = ce nom en `casefold()`.
- `register` rend `(operator, created)` : `created` permet au service de ne
  persister et publier que les créations.
- Événements accumulés puis vidés par `domain_events` (même patron que
  l'aggregate `Calibration`).
