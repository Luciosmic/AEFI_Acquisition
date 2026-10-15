# bar_transmission_calibration_panel — Intention

## Rationale

La calibration de la transmission par barre se fait au banc, par l'opérateur : il
pose la barre, saisit L, lance X, repositionne la barre, lance Y, puis décide
d'enregistrer en voyant la moyenne et l'écart X/Y. Sans onglet, la mesure n'aurait
aucun déclencheur ni aucun moyen de montrer la position en incréments — la seule
grandeur lisible quand le banc n'est pas calibré.

## Responsibility

- Afficher la position moteur X/Y en incréments, en direct, calibré ou non.
- Saisir L (mm) et l'axe ; boutons « Mesurer », « Annuler », « Enregistrer ».
- Afficher la progression (homing, fly scan, encadrements, affinage), le résultat de
  chaque axe (encadrements, N ± δ, transmission ± incertitude), la moyenne et l'écart
  X/Y, et les refus en clair.

## Design

- Widget passif : signaux vers le presenter, slots qui reçoivent des chaînes et des
  entiers ; aucun import du domaine ni du service.
- Version minimale (tranche testable au banc) : réglages (stabilisation, k, k_σ,
  vitesse, marge) et incertitude sur L pas encore exposés, valeurs par défaut.
- Pendant une mesure, seuls les boutons de l'onglet sont désactivés ; le scan est
  refusé par le contrôle exclusif des moteurs.
