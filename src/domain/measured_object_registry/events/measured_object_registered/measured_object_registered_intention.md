# measured_object_registered — Intention

## Rationale

Quand un objet mesuré est enregistré depuis un panneau, l'autre panneau (Scan
ou Continuous Reading) doit le proposer aussitôt. Sans fait publié, chaque
liste resterait figée jusqu'au redémarrage, ou devrait relire le registre en
permanence ; et le journal d'événements n'aurait aucune trace de ce qui a été
ajouté, ni quand.

## Responsibility

- Fait passé : un objet mesuré a été **créé** dans le registre (identité, nom,
  date d'enregistrement). Rejouable sans état courant (nom dénormalisé).

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- Émis par l'aggregate `MeasuredObjectRegistry`, uniquement à la création :
  enregistrer une orthographe déjà connue rend l'objet mesuré existant et
  n'émet rien (idempotence — un log, pas un événement).
- Topic : `"measuredobjectregistered"`.
