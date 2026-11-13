---
type: service-applicatif::solidai-hexagonal
tldr: "Service applicatif `inertial_probe_service` : Piloter la connexion/déconnexion de la carte via `IInertialProbeStreamPort`, en absorbant toute exception matérielle : `connect_sensor()` ne lève jamais, elle publie `InertialProbeConnectionChanged`."
code: ["[[src/application/inertial_probe/inertial_probe_service/inertial_probe_service.py]]"]
cause_de_changement: orchestration
---
# inertial_probe_service — Intention

## Rationale

Le banc doit un jour attendre sa stabilisation mécanique avant une mesure de
scan ; en attendant, l'opérateur doit voir en direct ce que le capteur inertiel
mesure pour juger si le montage est calme. Sans service dédié, la connexion à
la carte, le démarrage du flux et l'arrêt de sécurité à la fermeture seraient
éparpillés entre le presenter et le driver, et une carte débranchée finirait
par une exception dans le thread de l'interface.

## Responsibility

- Piloter la connexion/déconnexion de la carte via
  `IInertialProbeStreamPort`, en absorbant toute exception matérielle :
  `connect_sensor()` ne lève jamais, elle publie
  `InertialProbeConnectionChanged`.
- Démarrer/arrêter l'acquisition continue en déléguant à
  `IInertialProbeAcquisitionExecutor` (le démarrage du flux bloque ~0,5 s et
  tourne dans le thread de travail de l'exécuteur).
- `shutdown()` : arrêt de sécurité à la fermeture de l'application. La carte
  garde son flux actif port fermé ; le service arrête l'acquisition puis
  déconnecte, ce qui envoie `S*` à la carte.

## Design

- **Connexion et démarrage sont des actions demandées de l'extérieur** : le
  bouton du panneau, ou une fois au démarrage de l'application (pour la
  stabilisation de la colonne des scans), par le même chemin. Aucune
  reconnexion ni aucun redémarrage automatique ; l'arrêt de sécurité à la
  fermeture est automatique.
- Le capteur n'est pas une étape du démarrage matériel bloquant (une carte
  débranchée ne doit pas empêcher l'application de démarrer).
- Aucune calibration au repos appliquée : valeurs brutes converties
  uniquement.
- Gyroscope, magnétomètre et lidar sont des valeurs **non vérifiées**
  (pleine échelle gyroscope de 490 °/s reprise d'un VI, diviseur 2^15 contre
  2^16 du magnétomètre non tranché, lidar en mm non mesuré) ; le panneau le
  signale.
- **Dette non silencieuse** : le lidar mesure une distance, ce n'est pas un
  capteur inertiel. Il est ici un canal du même flux parce qu'il est sur la
  même carte et la même liaison série — considération d'infrastructure, pas de
  domaine. À terme, concept et port lidar séparés ; carte partagée = détail
  d'infrastructure. Voir `_system/ops/ponytail-debt.md`.
