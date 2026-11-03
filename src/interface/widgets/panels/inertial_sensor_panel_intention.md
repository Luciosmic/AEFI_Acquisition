# inertial_sensor_panel — Intention

## Rationale

Avant de pouvoir attendre la stabilisation mécanique du banc, l'opérateur doit
voir en direct ce que le capteur inertiel mesure, et surtout *savoir quelles
valeurs sont fiables* : trois des quatre canaux (gyroscope, magnétomètre,
lidar) reposent sur des facteurs non vérifiés. Un panneau qui afficherait des
nombres sans cet avertissement ferait passer des valeurs douteuses pour des
mesures.

## Responsibility

- Afficher, par canal, le libellé explicite, les valeurs par axe et, le cas
  échéant, le bandeau « valeur non vérifiée » avec sa raison et la note de
  dette (« canal provisoire : concept distinct à venir » pour le lidar).
- Afficher la cadence mesurée et le nombre d'échantillons.
- Émettre les demandes de l'opérateur : connecter, déconnecter, démarrer,
  arrêter. Connexion et démarrage ne sont jamais déclenchés automatiquement.
- Indiquer l'état (non connecté, connecté, acquisition en cours, flux en
  échec avec sa raison).

## Design

- Le widget ne reçoit que des booléens, des chaînes et le view model gelé
  (`InertialSensorReadingViewModel`) : aucun import de `domain/`.
- Les lignes sont construites depuis les descripteurs statiques du view model :
  les libellés et les avertissements sont visibles avant la première valeur.
- Aucun graphique à ce stade : valeurs courantes seulement (incrément
  « afficher en direct »).
