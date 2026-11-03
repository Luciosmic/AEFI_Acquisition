# inertial_sensor_service — Intention

## Rationale

Le banc doit un jour attendre sa stabilisation mécanique avant une mesure de
scan ; en attendant, l'opérateur doit voir en direct ce que le capteur inertiel
mesure pour juger si le montage est calme. Sans service dédié, la connexion à
la carte, le démarrage du flux et l'arrêt de sécurité à la fermeture seraient
éparpillés entre le presenter et le driver, et une carte débranchée finirait
par une exception dans le thread de l'interface.

## Responsibility

- Piloter la connexion/déconnexion de la carte via
  `IInertialSensorStreamPort`, en absorbant toute exception matérielle :
  `connect_sensor()` ne lève jamais, elle publie
  `InertialSensorConnectionChanged`.
- Démarrer/arrêter l'acquisition continue en déléguant à
  `IInertialSensorAcquisitionExecutor` (le démarrage du flux bloque ~0,5 s et
  tourne dans le thread de travail de l'exécuteur).
- `shutdown()` : arrêt de sécurité à la fermeture de l'application. La carte
  garde son flux actif port fermé ; le service arrête l'acquisition puis
  déconnecte, ce qui envoie `S*` à la carte.

## Design

- **Connexion et démarrage restent des actions de l'opérateur** : aucune
  automatisation cachée (pas de reconnexion ni de redémarrage automatique).
  Seul l'arrêt de sécurité à la fermeture est automatique.
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
