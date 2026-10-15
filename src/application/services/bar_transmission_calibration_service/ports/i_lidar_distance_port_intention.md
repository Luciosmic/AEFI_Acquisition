# i_lidar_distance_port — Intention

## Rationale

Le LIDAR est un canal du flux de la carte inertielle (`IInertialSensorStreamPort`),
piloté par le panneau du capteur. Si la calibration utilisait ce port directement,
elle hériterait de tout le flux inertiel et de son exécuteur ; et deux lecteurs sur
le même port série se voleraient les lignes. Il faut un port étroit, du point de vue
de la calibration : « une distance, quand elle est arrivée », et un propriétaire
unique du flux.

## Responsibility

- Ouvrir le flux LIDAR (refus `LidarStreamBusyError` si le panneau le diffuse déjà),
  lire les distances horodatées à leur réception, fermer le flux dans tous les cas.

## Design

- Port sortant placé dans le dossier du service consommateur.
- Horodatage à la réception (pas à la lecture) : le service attend la stabilisation
  sans lire, puis ne garde que les distances arrivées après.
- Erreurs déclarées : `LidarStreamBusyError`, `LidarUnavailableError`
  (`lidar_stream_error.py`).
- Qualité de service : ~25 Hz mesuré sur la carte (journal 2026-10-12) ; le service
  ne suppose pas de cadence, il attend des échantillons avec un délai de silence.
