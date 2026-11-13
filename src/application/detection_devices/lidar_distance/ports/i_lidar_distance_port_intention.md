# i_lidar_distance_port — Intention

## Rationale

Le LIDAR est un canal du flux de la carte inertielle (`IInertialProbeStreamPort`),
piloté par le panneau du capteur. Si la calibration utilisait ce port directement,
elle hériterait de tout le flux inertiel et de son exécuteur ; et deux lecteurs sur
le même port série se voleraient les lignes. Il faut un port étroit, du point de vue
de la calibration : « une distance, quand elle est arrivée », et un propriétaire
unique du flux.

## Responsibility

- Ouvrir le flux LIDAR (refus `LidarStreamBusyError` si le panneau le diffuse déjà),
  lire les distances horodatées à leur réception, fermer le flux dans tous les cas.
- Ne livrer que des distances valides ou des « pas de retour » explicites : chaque
  lecture porte un `LidarDistance` du noyau partagé (le LIDAR renvoie 0 quand il
  ne mesure rien ; premier essai au banc, 2026-10-15 : le sol hors de portée ne
  renvoie que des 0, la barre a des décrochages). Un 0 n'est jamais une
  distance ; il n'est pas non plus supprimé, car hors barre il est la seule trace
  du sol. La règle du 0 vit dans `LidarDistance`, pas dans le port ni
  l'adaptateur.

## Design

- Port sortant placé dans un dossier neutre `application/detection_devices/lidar_distance/ports/`
  (même chemin que le pilote autonome LIDAR-VL53L0C-ESP32) : son premier consommateur,
  la calibration par barre, a été abandonné le 2026-10-30 ; le port reste pour tout
  lecteur du LIDAR, quel que soit le capteur derrière.
- Horodatage à la réception (pas à la lecture) : le service attend la stabilisation
  sans lire, puis ne garde que les distances arrivées après.
- Erreurs déclarées : `LidarStreamBusyError`, `LidarUnavailableError`
  (`lidar_stream_error.py`).
- Qualité de service : ≈ 5,1 Hz (185 à 208 ms) mesuré sur l'ESP32 le 2026-10-30
  (25 Hz pour le LIDAR de la carte inertielle, journal AEFI 2026-10-12) ; le service
  ne suppose pas de cadence, il attend des échantillons avec un délai de silence.
