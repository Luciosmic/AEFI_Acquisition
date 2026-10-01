# line_scan_config — Intention

## Rationale

Sans ce module, un scan 1D ne peut s'exprimer qu'en détournant une grille `ScanZone` à une seule rangée, ce qui signifie qu'une ligne verticale (theta=90°, extension X nulle) est rejetée par l'invariant strict `x_min < x_max`, et qu'une ligne diagonale est impossible — ce qui force soit à affaiblir l'invariant de `ScanZone` pour tous les scans, soit à renoncer aux profils orientés pourtant nécessaires à l'analyse du champ entre sphères.

## Responsibility

- Décrire une ligne de scan dans le plan XY : centre, longueur, nombre de points, angle theta.
- Valider : `n_points >= 1`, `length_mm > 0`, les deux extrémités de la ligne dans les limites physiques X/Y, réglages d'exécution positifs.

## Design

- `@dataclass(frozen=True)`, validation dans `__post_init__`.
- Paramétrisation : `x(s) = center.x + s·cos(theta)`, `y(s) = center.y + s·sin(theta)`, `s ∈ [-length/2, +length/2]`. theta=0° → X pur, 90° → Y pur.
- La boîte englobante est validée via les extrémités (une ligne est convexe), **pas via `ScanZone`**.
- Porte les réglages par point lus par la boucle de scan (`stabilization_delay_ms`, `averaging_per_position`, `differential_mode`, `differential_settle_delay_ms`), mêmes sens et mêmes contrôles que `StepScanConfig` — dupliqués volontairement (marqueur `ponytail:`), à extraire en VO commun si un 3e type de scan en a besoin.
- `total_points()` : même contrat que `StepScanConfig`, lu par `StepScan.start()`.
