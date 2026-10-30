# inertial_sensor_connection_changed — Intention

## Rationale

La carte du capteur inertiel peut être débranchée ou absente : elle n'est pas
une étape du démarrage matériel bloquant, la connexion est une commande
explicite de l'opérateur. Sans un événement unique pour les trois issues
(connecté, déconnecté, échec de connexion), le panneau devrait deviner l'état
de la liaison à partir de l'absence d'échantillons.

## Responsibility

- Signaler un changement d'état de connexion : `connected=True`, ou
  `connected=False` avec un message d'erreur optionnel (port absent, délai
  dépassé).

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- `error: Optional[str]` — présent seulement en cas d'échec.
- Topic de publication : `"inertialsensorconnectionchanged"`.
