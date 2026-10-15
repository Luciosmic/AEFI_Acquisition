# bar_transmission_calibration_presenter — Intention

## Rationale

La mesure d'un axe tourne plusieurs minutes hors du thread Qt et rend des DTO
d'application ; l'onglet ne doit importer ni le domaine ni le service, et ne doit
jamais être touché depuis le thread de mesure. Sans presenter, l'onglet devrait
connaître le service, le bus d'événements et les DTO, et l'opérateur verrait un
écran figé pendant la mesure.

## Responsibility

- Transmettre « Mesurer » (axe, L), « Annuler », « Enregistrer » au service ; L'incertitude
  sur L et les réglages restent pour l'instant à leurs valeurs par défaut (0 mm,
  `BarCalibrationSettingsDTO()`).
- Port de sortie : progression, résultat d'un axe, échec — uniquement des signaux.
- Garder la dernière mesure de chaque axe, pour `record(X, Y)` : « Enregistrer » ne
  fait rien tant que les deux axes ne sont pas mesurés (seule voie d'écriture).
- Afficher la moyenne et l'écart X/Y dès que les deux axes sont mesurés (`compare`),
  puis après l'enregistrement.
- Relayer la position moteur en incréments (`motorincrementsupdated`), calibré ou non.

## Design

- `QObject` + `IBarTransmissionCalibrationOutputPort`, enregistré comme port de sortie
  dans `__init__`.
- Les textes sont formatés ici (présentation pure : aucune valeur métier calculée) ;
  l'onglet ne reçoit que des chaînes et des entiers.
