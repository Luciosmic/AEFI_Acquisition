# bar_transmission_calibration_service — Intention

## Rationale

`travel_per_motor_revolution_mm` est supposée, jamais mesurée : son erreur devient
une erreur d'échelle de toute la cartographie. Une barre de longueur L vue par le
LIDAR donne un créneau dont l'écart entre les fronts, en incréments, donne la
transmission. Sans service qui orchestre la mesure, l'opérateur devrait enchaîner à
la main homing, fly scan, lecture des plateaux et dichotomie au clavier, et
l'écriture de la transmission resterait une saisie libre, sans incertitude ni écart
X/Y.

Spécification : `_system/documentation/l-ecart-en-impulsions-entre-les-deux-fronts-lidar-d-une-barre-de-longueur-connue-donne-la-transmission-du-banc.md`.

## Responsibility

- `measure_axis(axe, L, ΔL, réglages)` : refus immédiat et typé si les moteurs sont tenus\r
  (un scan tourne), si une mesure tourne, si la chaîne (pas par tour, micro-pas) est incomplète, si le
  panneau capteur diffuse déjà le flux LIDAR, ou si la demande est invalide. Sinon,
  hors thread Qt :
  1. ouvrir le flux LIDAR (la calibration le démarre elle-même) ;
  2. homing de l'axe ;
  3. fly scan de la butée d'origine à la butée + (fin de course physique) : couples
     incréments/distance horodatés à la réception, appariés par le temps ;
  4. plateaux, seuil et fronts grossiers (`bar_profile_analysis`) ;
  5. encadrements grossiers élargis d'une marge v·τ, vérifiés à l'arrêt (élargis
     encore s'ils ne se confirment pas) ;
  6. affinage des deux fronts à l'arrêt par dichotomie (stabilisation, k
     retours valides reçus après la stabilisation, classification) ;
  7. résultat N ± δ, transmission ± incertitude ; retour de l'axe à l'origine ;
  8. arrêt du flux LIDAR **dans tous les cas**.
- `cancel_measurement()` : arrêter l'axe et abandonner.
- `record(X, Y)` : nouvelle `MechanicalTransmissionCalibrationEntry` avec la moyenne
  X/Y de `travel_per_motor_revolution_mm`, micro-pas et courants repris de l'entrée
  courante ; publie `mechanicaltransmissioncalibrationentryadded`. Seule voie
  d'écriture, déclenchée par l'opérateur.
- `compare(X, Y)` : moyenne et écart sans rien écrire.

## Design

- Ports : `IRawIncrementMotionPort` (incréments bruts), `ILidarDistancePort`,
  repositories du domaine (transmission, composants) — jamais
  `MechanicalTransmissionCalibrationService` (pas d'appel de service à service).
- Calcul dans le domaine (`EdgeBracket`, `BarPointReading`, `bar_profile_analysis`,
  `AxisBarTransmissionMeasurement`, `BarTransmissionMean`) ; le service orchestre.
- Seul site de traduction des erreurs : ports et domaine → union
  `BarTransmissionCalibrationError`, présentée par le port de sortie.
- Exclusion par le mécanisme du projet, comme `sensor_calibration_service` :\r
  `take_all` sur les `ExclusiveControl` des moteurs (partagé avec le scan, qui le\r
  prend aussi : scan et calibration se refusent mutuellement) et du flux LIDAR\r
  (partagé avec le panneau capteur, qui refuse alors démarrage et déconnexion),\r
  tenus toute la mesure, relâchés dans tous les cas. Le refus est repris tel quel\r
  (`BenchResourceControlled`). En plus, refus si l'exécuteur du panneau diffuse\r
  déjà le flux.
- Réglages : constantes nommées par défaut (`BarCalibrationSettingsDTO`),
  surchargeables depuis l'interface, valeurs initiales à ajuster sur le banc.
  Vitesse de repositionnement (préréglage « fast »), délais et nombre
  d'élargissements : constantes du module.
- Horloge injectée (`now`, `sleep`) : `perf_counter` au banc, la même que celle qui
  horodate les distances LIDAR ; horloge virtuelle en test.
- Aller-retour libre pendant la dichotomie (décision du 2026-10-15) : aucun sens
  d'approche imposé, le jeu n'est pas compensé.
- « Pas de retour » LIDAR (le capteur envoie 0 quand il ne mesure rien ; premier
  essai au banc, 2026-10-15 : le sol hors de portée ne renvoie que des 0, la barre
  a des décrochages) : la règle vit dans le value object `LidarDistance` du noyau
  partagé, la classification et la moyenne sur les seuls retours valides dans
  `BarPointReading` et `bar_profile_analysis` ; le service ne fait qu'orchestrer.
  Un point à l'arrêt attend ses k retours valides pendant au plus
  `POINT_READ_TIMEOUT_FACTOR` × k / 25 Hz ; au-delà le domaine le classe sur ce
  qu'il a reçu (aucun retour : hors barre ; quelques-uns : indécidable). Le silence total
  du flux reste une panne (`LIDAR_SILENCE_S`), jamais une boucle sans fin. Nombre
  de 0 logué de façon agrégée (`rejected_zero=`) : en DEBUG par point, dans le
  bilan du fly scan — jamais une ligne par échantillon.
- Logs d'intention à chaque étape avec l'identifiant de mesure et l'axe.
- Les commandes manuelles du panneau Mouvement ne prennent pas le contrôle des\r
  moteurs : elles ne sont pas bloquées pendant la mesure (point ouvert).
