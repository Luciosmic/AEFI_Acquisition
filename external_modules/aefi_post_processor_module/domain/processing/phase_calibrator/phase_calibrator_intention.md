---
type: atome::solidai-atome
tldr: "Faire tourner le champ pour annuler la quadrature au point de référence, en gardant le signe de la composante en phase."
code: ["[[external_modules/aefi_post_processor_module/domain/processing/phase_calibrator/phase_calibrator.py]]"]
cause_de_changement: regle-metier
---
# phase_calibrator — Intention

## Rationale

La chaîne de mesure déphase le signal de chaque axe de façon inconnue. Sans calibration, la quadrature contient une partie du signal utile et les cartes d'amplitude ne sont pas comparables d'un scan à l'autre.

## Responsibility

- Calculer l'angle de phase de chaque axe au point de référence, et le point valide le plus proche si la référence est NaN.
- Appliquer la rotation (et l'inversion de signe si la composante en phase de référence est négative) à tout le champ.
- Rendre les angles utilisés et le point de référence réellement retenu.

## Design

- Classe `PrimaryFieldPhaseCalibrator` ; `border_width` est conservé pour la compatibilité mais ne sert plus.
- Deux échecs connus dans `_tests/phase_calibration_test.py` (écart de 180° sur x et y, `extract_border_pixels` absent) ; ils décrivent l'ancienne méthode par la bordure, qu'on ne rétablit pas : la tranche 5 du plan les traite.
