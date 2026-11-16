---
type: atome::solidai-atome
tldr: "La grille qu'une acquisition a prévue pour un scan : zone et nombre de points par axe, et le nœud le plus proche de chaque point mesuré."
code: ["[[external_modules/aefi_post_processor_module/domain/processing/planned_scan_grid/planned_scan_grid.py]]"]
cause_de_changement: regle-metier
---
# planned_scan_grid — Intention

## Rationale

Les points mesurés ne disent pas la forme prévue d'un scan : un scan rectangulaire complet (150 × 100) et un scan carré interrompu au bout de 100 lignes donnent les mêmes coordonnées. Seule la description de l'acquisition le dit. Sans valeur qui porte la grille prévue, la mise en grille devait deviner, et elle complétait tout scan en carré : un scan rectangulaire s'affichait avec une bande vide de l'autre côté (constaté le 2026-11-16 sur le scan de la bouteille d'eau du 13 novembre).

## Responsibility

- Porter la grille prévue : par axe, la première et la dernière position et le nombre de points, nœuds régulièrement espacés, extrémités comprises.
- Refuser un axe sans point, ou de plusieurs points sans étendue.
- Rendre, pour des coordonnées mesurées, l'indice du nœud le plus proche, ou rien si une coordonnée tombe à plus d'un demi-pas de tout nœud : la grille ne décrit alors pas ces points.

## Design

- Deux valeurs figées, `PlannedAxis` et `PlannedScanGrid`, sur numpy seul ; la lecture du fichier de l'acquisition reste à l'infrastructure.
- Le pas d'un axe à un seul nœud vaut 1.0, comme dans la grille construite sur les points mesurés.
