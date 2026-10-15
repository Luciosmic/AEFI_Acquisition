# lsm9ds1_conversion — Intention

## Rationale

La carte renvoie des entiers bruts signés sur 16 bits ; sans conversion
séparée, les pleines échelles (dont deux ne sont pas vérifiées) seraient
dispersées entre le driver et l'adaptateur, et corriger l'une d'elles
demanderait de chasser des constantes dans plusieurs fichiers. La conversion est
faite côté PC (comme le VI LabVIEW : pleine échelle / 2^15) ; on la sépare de
l'I/O pour la vérifier sans matériel.

## Responsibility

- Constantes de pleine échelle : accéléromètre ±2 g (déduit : le VI annonce 4 g
  mais |a| au repos donnait 2,07 g), gyroscope 490 °/s (repris d'un VI,
  **non vérifié**), magnétomètre 400 µT (diviseur 2^15 ou 2^16 **non tranché** :
  avec 2^16 le champ au repos vaut 25 µT, la moitié du champ terrestre attendu).
- `raw_to_physical(raw, full_scale)` : `brut × pleine échelle / 2^15`.
- `lidar_raw_to_mm(raw)` : point unique de conversion du lidar. Facteur
  `LIDAR_MM_PER_LSB = 1.0` : l'unité (mm) vient de l'utilisateur, **non
  mesurée** ; facteur et offset à vérifier face à des distances connues.

## Design

- Pure, sans état.
- Aucune calibration au repos appliquée : le facteur 0,9673 de la source vient
  d'une seule orientation et n'est pas une calibration complète. Valeurs brutes
  converties uniquement.
- Le lidar est converti ici parce qu'il traverse le même flux ; c'est une dette
  `ponytail:` (voir le module).
