# esp32_serial_lidar (ESP32 série) — Intention

## Rationale

La calibration de la transmission moteur mesure la linéarité mm/incrément et les
pas ratés avec un LIDAR fixé sur la colonne, qui s'approche pas à pas d'un
obstacle fixe. Ce LIDAR n'est plus celui de la carte inertielle : c'est un
capteur lu par un ESP32 sur son propre port série, et d'autres LIDAR suivront,
tous derrière un ESP32 au même format texte. Sans un adaptateur nommé d'après
ce protocole, chaque nouveau capteur amènerait son propre code de lecture, et
la calibration finirait par savoir quel LIDAR elle lit — alors qu'elle ne doit
dépendre que de `ILidarDistancePort`. Et comme pour l'ancien LIDAR, si la
calibration lisait le port seulement quand elle en a besoin, les distances
accumulées pendant un déplacement sortiraient avec l'heure de la lecture :
impossible de savoir lesquelles ont été mesurées après l'arrêt du moteur.

## Responsibility

- Implémenter `ILidarDistancePort` sur un port série tenu par un ESP32 qui émet
  en continu, sans commande. Une instance par LIDAR physique : port COM et
  débit sont des paramètres du constructeur.
- Lire en continu dans un thread dédié, horodater chaque ligne à sa réception
  (`time.perf_counter`, l'horloge du service), la mettre en file.
- Ne garder que la colonne 1 (distance brute) ; construire la `LidarDistance`
  avec `LidarDistance.from_raw` : la règle « 0 = pas de retour » vit dans ce
  value object du noyau partagé, comme pour l'ancien LIDAR.
- Ignorer les lignes illisibles sans jamais lever vers l'appelant ; les compter.
- Traduire les erreurs série en `LidarUnavailableError` (ouverture impossible —
  port absent ou tenu par un autre processus — ou 3 lectures consécutives en
  échec, même tolérance que l'adaptateur de la carte inertielle).

## Design

- Protocole observé au banc le 2026-10-30, firmware ESP32 non documenté :
  115200 Bd 8N1 (pour le premier capteur), lignes ASCII `"<brut> <moyenne>\r\n"`,
  ex. `1227 1230`, ≈ 5 Hz irrégulier (63 à 404 ms entre lignes), σ ≈ 6.6 au
  repos (bruit blanc), aucun 0 observé.
- Colonne 2 ignorée : c'est la moyenne glissante des 10 dernières valeurs
  brutes calculée par l'ESP32 ; elle garde ≈ 2 s de mémoire après un
  déplacement et fausserait la stabilisation et l'écart-type que la
  calibration calcule elle-même sur les valeurs brutes. Elle doit quand même
  être un entier : une ligne à une seule colonne est illisible.
- Unité supposée mm (`MM_PER_LSB = 1.0`), **non vérifiée** ; la calibration n'en
  dépend pas.
- La première ligne après ouverture est jetée : le port s'ouvre au milieu d'une
  ligne, et un fragment `27 1230` passerait pour une distance.
- Un tampon sans fin de ligne au-delà de 64 octets est jeté comme ligne illisible.
- `is_streamed_elsewhere()` vaut toujours `False` : le port série appartient à
  cet adaptateur seul ; un autre processus qui le tient fait échouer `open()`.
- Compteurs (`readings=`, `rejected_zero=`, `unreadable_lines=`) logués une fois,
  à l'arrêt du lecteur ; chaque ligne illisible seulement en DEBUG.
- Fabrique de port série injectée (`serial_factory`, comme
  `LSM9DS1StreamDriver`) : les tests passent un faux port série, sans matériel.
- Premier capteur derrière ce protocole : VL53L0X sur COM9 (banc, 2026-10-30).
