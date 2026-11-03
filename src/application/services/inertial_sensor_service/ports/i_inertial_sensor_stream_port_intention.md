# i_inertial_sensor_stream_port — Intention

## Rationale

Sans port, le service applicatif importerait le driver série de la carte :
changer de carte ou de firmware réécrirait le service, et aucun test
applicatif ne tournerait sans port COM. Le flux continu est aussi incompatible
avec un mode requête/réponse sur la même liaison (un flux actif renvoie une
ligne de flux à la place de la réponse), donc le contrat du flux a son propre
port.

## Responsibility

- `connect()` / `disconnect()` (idempotent, envoie l'arrêt du flux) /
  `is_connected()`.
- `start_stream(channels)` : démarre le flux d'un sous-ensemble de canaux.
  Bloque ~0,5 s sur la vraie carte.
- `stop_stream()`.
- `read_sample(timeout_s)` : lecture bloquante, `None` sur timeout.

## Design

- **Port outbound** (Application vers Infrastructure) dans
  `inertial_sensor_service/ports/`.
- Lecture bloquante, sans thread ni callback : le thread appartient à
  l'exécuteur d'acquisition.
- **Dette non silencieuse** : le lidar est un canal de ce même flux parce qu'il
  est sur la même carte et la même liaison série (fait d'infrastructure). Ce
  n'est pas un capteur inertiel. Sortie : un port lidar séparé, la carte
  partagée restant un détail d'infrastructure.
