# sensor_mounting_solver — Intention

## Rationale

Sans ce solveur, les angles de montage P ne s'obtiennent que par tâtonnement
sur trois spinbox, en regardant le signal ramené au repère sources. Le
résultat dépend alors de l'opérateur (quand s'arrête-t-il ? quel compromis
entre « E_y min » et « E_z min » ?) et n'est pas reproductible : deux
calibrations du même montage donnent deux P différents. Le critère du
protocole manuel est pourtant précis — il manquait sa formulation
mathématique, et donc son optimum.

## Responsibility

- À partir des réponses du capteur (repère capteur) à l'excitation selon X et
  selon Y, trouver P tel que `P·r_X` soit au plus près de `+e_x^sources` et
  `P·r_Y` au plus près de `+e_y^sources` — le critère de la procédure de
  `rotation_convention_intention.md`, au sens des moindres carrés.
- Rendre la qualité de l'ajustement : désalignement résiduel de chaque
  réponse (°) et angle entre les deux réponses (idéalement 90°).
- Refuser des réponses qui ne déterminent pas P (nulles, ou trop proches de
  la colinéarité) : `SensorResponseDegenerateError`.

## Design

- Problème de Wahba : `min_P Σ ||P·u_i − v_i||²` avec `u_i` les réponses
  normalisées et `v_i ∈ {e_x, e_y}`. Solution exacte par SVD
  (`scipy.spatial.transform.Rotation.align_vectors`) — ce n'est pas la
  « formule fermée » rejetée par la convention (qui supposait un champ
  primaire idéal) : on optimise le critère sur le champ réellement mesuré.
  Si les deux réponses ne sont pas orthogonales (asymétries du montage des
  sphères), l'écart est réparti à parts égales entre X et Y.
- Réponses normalisées : seule la direction compte, l'amplitude (gain,
  niveau d'excitation) n'influence pas P.
- Cibles `+e_x` pour X_DIR et `+e_y` pour Y_DIR : sur le carré idéal, la
  phase S1/S2 à 180° (X_DIR) donne un champ selon +x^sources, à 0° (Y_DIR)
  selon +y^sources. Le signe suppose la référence de détection synchrone
  calibrée (phase DDS3/DDS1) : une référence inversée de 180° inverse les
  deux réponses et donne un P tourné de 180°.
- Seuil de séparation `MIN_RESPONSE_SEPARATION_DEGREES` (45°) : bouton de
  réglage, pas une loi physique — en dessous, P est mal déterminé (bruit).
- Pas d'I/O, pas d'état : fonction pure.
