# source_geometry — Intention

## Rationale

Ce qu'on peut mesurer directement sur le banc AEFI 4 sphères, ce n'est ni le centre des sphères (inaccessible au pied à coulisse) ni la distance centre-à-centre : ce sont les distances **extrémité-à-extrémité** entre sphères ($D_{ij}$) et le **diamètre de chaque sphère** ($\phi_i$), mesurés individuellement. `SourceGeometry` porte cette donnée brute mesurable, telle quelle. Voir "NOTE - Source Frame Geometry" (vault Luis Saluden, hors dépôt).

## Responsibility

- Stocker les 6 distances extrémité-à-extrémité `D_12, D_13, D_14, D_23, D_24, D_34` (mètres) et les 4 diamètres `phi_1..phi_4` (mètres).
- Valider que chaque grandeur brute est finie et strictement positive.
- Exposer les grandeurs dérivées en lecture seule : `r_i = phi_i / 2` et `d_ij = D_ij - r_i - r_j` (distance centre-à-centre, consommée par `SourceFrameSolver`).
- Valider que chaque `d_ij` dérivé reste positif (sphères mesurées comme se chevauchant = erreur de mesure).

## Design

- `@dataclass(frozen=True)` — immuable, ne stocke que ce qui a été réellement mesuré.
- `r_i` et `d_ij` sont des `@property` calculées, jamais des champs stockés — la config ne doit jamais encoder une grandeur dérivée.
- Pas de logique de reconstruction ici : la validation géométrique fine (triangle dégénéré) est de la responsabilité du solveur, pas de ce VO.
