# inertial_sensor_stream_failed — Intention

## Rationale

La carte peut cesser d'émettre ou la liaison série peut tomber en cours
d'acquisition. Sans événement d'échec, le panneau continuerait d'afficher la
dernière valeur comme si elle était courante, et le futur détecteur de
stabilité prendrait un silence pour du calme.

## Responsibility

- Signaler que le flux d'acquisition s'est arrêté sur un échec, après la
  tolérance aux échecs consécutifs, avec la raison en texte.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- `acquisition_id: UUID` et `reason: str`.
- Topic de publication : `"inertialsensorstreamfailed"`.
- Un arrêt demandé par l'opérateur ne produit pas cet événement.
