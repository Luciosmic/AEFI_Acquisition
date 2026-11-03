# operator_registered — Intention

## Rationale

Quand un opérateur est enregistré depuis un panneau, l'autre panneau (Scan
ou Continuous Reading) doit le proposer aussitôt. Sans fait publié, chaque
liste resterait figée jusqu'au redémarrage, ou devrait relire le registre en
permanence ; et le journal d'événements n'aurait aucune trace de qui a été
ajouté, ni quand.

## Responsibility

- Fait passé : un opérateur a été **créé** dans le registre (identité, nom,
  date d'enregistrement). Rejouable sans état courant (nom dénormalisé).

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- Émis par l'aggregate `OperatorRegistry`, uniquement à la création :
  enregistrer une orthographe déjà connue rend l'opérateur existant et
  n'émet rien (idempotence — un log, pas un événement).
- Topic : `"operatorregistered"`.
