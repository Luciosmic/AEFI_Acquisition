# i_raw_increment_motion_port — Intention

## Rationale

Avant calibration, `IMotionPort` refuse tout mouvement en millimètres : il n'a pas
de conversion. Or la calibration par barre doit déplacer le banc précisément pour
mesurer cette conversion. Si elle passait par les millimètres, la mesure dépendrait
de la valeur mesurée ; si elle appelait le driver Arcus directement, le service
applicatif dépendrait de l'infrastructure et ne serait testable qu'avec le banc.

## Responsibility

- Piloter un axe en incréments moteur bruts : homing, aller à un incrément, courir
  jusqu'à la butée + (fin de course physique), vitesse en incréments/s, lire la
  position, arrêter, attendre l'arrêt.
- Dire si le fin de course + est actif.

## Design

- Port sortant placé dans un dossier neutre `application/services/raw_increment_motion/ports/`
  (même chemin que le pilote autonome Arcus-Performax-4EX) : son premier consommateur,
  la calibration par barre, a été abandonné le 2026-10-30 ; le port reste pour tout
  usage qui doit bouger le banc en incréments bruts.
- Échec de contrôleur ou de liaison : `RawIncrementMotionError`, erreur déclarée par
  le port ; l'adaptateur traduit les exceptions du driver.
- `move_to` / `run_to_positive_limit` rendent la main tout de suite (le fly scan
  interroge la position pendant le mouvement) ; `home` / `wait_until_stopped`
  bloquent.
- Concurrence : le contrôleur est partagé avec l'adaptateur mm (`ArcusAdapter`) ;
  le driver sérialise chaque échange série (RLock), donc ce port et le moniteur de
  position de l'adaptateur mm peuvent fonctionner en même temps. Le moniteur reste
  actif pendant la calibration pour afficher la position en incréments.
  `wait_until_stopped` interroge `is_moving` au lieu de bloquer le driver, pour ne
  pas geler ce moniteur.
- Qualité de service : le fly scan apparie distances et positions par leur instant
  de réception ; la latence d'une lecture de position (requête série) ne touche que
  le repérage grossier, absorbé par la marge.
