# bar_transmission_calibration_error — Intention

## Rationale

La calibration par barre échoue pour des raisons qui appellent des gestes
opérateur différents : arrêter le flux du panneau capteur, vérifier un fin de
course, reposer la barre, attendre la fin d'un scan, caractériser le moteur. Une
chaîne de caractères ne permettrait pas au panneau de distinguer ces cas, et une
exception non typée ferait tomber la tâche de fond sans rien dire.

## Responsibility

- Énumérer les échecs de `measure_axis`, `record` et `compare` : mesure déjà en
  cours, ressource tenue par un autre propriétaire (moteurs pendant un scan, flux LIDAR — refus d'`ExclusiveControl` repris tel quel), flux LIDAR déjà diffusé par le panneau, LIDAR indisponible, chaîne de
  mouvement incomplète, demande invalide, mouvement en échec, butée + non atteinte,
  barre non trouvée, encadrement non vérifié, annulation, mesures X/Y non
  combinables, erreur interne.
- `message` : texte opérateur, le presenter n'inspecte pas les variantes.

## Design

- Union scellée (classe de base + dataclasses figées), sur le modèle de
  `MotionControlError`.
- Le service applicatif est le seul site de traduction : erreurs des ports
  (`RawIncrementMotionError`, `LidarStreamBusyError`, `LidarUnavailableError`) et
  du domaine (`BarProfileUnusableError`, `ValueError` des invariants) deviennent des
  variantes de cette union.
