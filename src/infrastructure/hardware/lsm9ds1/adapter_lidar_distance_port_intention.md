# adapter_lidar_distance_port — Intention

## Rationale

Le LIDAR passe par le flux de la carte inertielle, et le driver horodate une ligne
au moment où elle est **lue**, pas quand elle arrive. Si la calibration lisait le
flux seulement quand elle en a besoin, les distances accumulées pendant un
déplacement ou une stabilisation sortiraient toutes avec l'heure de la lecture :
impossible de savoir lesquelles ont été mesurées après l'arrêt du moteur. Et sans
contrôle du propriétaire, la calibration et le panneau du capteur liraient le même
port série en même temps.

## Responsibility

- Implémenter `ILidarDistancePort` sur `IInertialProbeStreamPort`, canal LIDAR seul.
- Refuser l'ouverture (`LidarStreamBusyError`) tant que l'exécuteur d'acquisition du
  panneau tourne.
- Connecter la carte si elle ne l'est pas (et la déconnecter à la fermeture dans ce
  cas seulement), démarrer le flux LIDAR, l'arrêter à la fermeture (la carte
  continue sinon).
- Lire en continu dans un thread dédié, mettre chaque distance en file avec son
  instant de réception.
- Reprendre la `LidarDistance` de chaque échantillon du flux, construite une seule
  fois par l'adaptateur du flux inertiel avec `LidarDistance.from_raw` : la règle
  « 0 = pas de retour » (premier essai au banc, 2026-10-15 : sol hors de portée,
  décrochages) vit dans ce value object du noyau partagé, pas ici.
- Traduire les erreurs série en `LidarUnavailableError` (après la même tolérance que
  l'exécuteur du panneau : 2 erreurs consécutives).

## Design

- Thread démon, arrêté par drapeau + `join` ; `close()` idempotent.
- Nombre de « pas de retour » logué une fois, à l'arrêt du
  lecteur (`rejected_zero=`), jamais une ligne par échantillon.
- L'unité du LIDAR (mm, non vérifiée) vient de `LIDAR_MM_PER_LSB` ; la calibration
  n'en dépend pas (seul le seuil compte).
- ponytail: le LIDAR reste un canal du flux inertiel (voir
  `IInertialProbeStreamPort`) ; cet adaptateur est la frontière qui disparaîtra le
  jour où le LIDAR aura son propre port.
