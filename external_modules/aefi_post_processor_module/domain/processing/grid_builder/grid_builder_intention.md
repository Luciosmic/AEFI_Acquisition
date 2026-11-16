---
type: atome::solidai-atome
tldr: "Placer les points d'un scan sur la grille que l'acquisition a prévue, NaN là où rien n'a été mesuré ; à défaut de grille prévue, sur une grille carrée, sans dépendre de pandas."
code: ["[[external_modules/aefi_post_processor_module/domain/processing/grid_builder/grid_builder.py]]"]
cause_de_changement: regle-metier
---
# grid_builder — Intention

## Rationale

Un scan interrompu et un scan rectangulaire donnent les mêmes points mesurés, mais pas la même carte : l'interrompu doit montrer ce qui manque, le rectangulaire ne manque de rien. Seule la grille prévue par l'acquisition les distingue. Tant que la mise en grille complétait tout scan en carré, un scan rectangulaire complet s'affichait avec une bande vide (le scan de 150 × 100 points du 13 novembre 2026 montrait 50 lignes vides au-dessus de y = 781 mm).

Tant que cette mise en grille vivait dans une classe qui lit un `DataFrame` pandas, le domaine ne pouvait pas la porter, et les chiffres de l'extension de la carte (`extent`) dépendaient d'un lecteur de CSV.

## Responsibility

- `build_scan_grid` : rendre la grille d'un scan et son origine (`GridOrigin`) ; la grille prévue quand elle est connue et contient chaque point, sinon la grille carrée.
- `build_planned_grid` : une grille `(points y prévus, points x prévus, canaux)` indexée `[y, x, canal]`, NaN où aucun point n'existe ; l'`extent` est celle des cellules de la grille prévue. Rien si un point tombe hors de la grille prévue.
- `build_square_grid` : une grille `(N, N, canaux)` avec `N = max(nx, ny)` ou la taille demandée, pour un scan dont on ne connaît pas la grille prévue (scans synthétiques, scans sans description). Inchangée : l'étalon `golden_master_test` la garde.
- Rendre les métadonnées de la grille : `extent` (bords des cellules), coordonnées, pas, nombres de points valides et totaux.
- Refuser un scan sans canal.

## Design

- Fonctions sur des tableaux numpy ; la lecture du CSV et celle de la description de l'acquisition restent aux appelants.
- La grille prévue arrive comme valeur du domaine (`PlannedScanGrid`) ; chaque point va au nœud prévu le plus proche.
- Un point hors de la grille prévue fait revenir à la grille carrée plutôt que de le jeter : l'origine `points_off_plan` le dit, et l'appelant le journalise.
- Le pas de la grille carrée est la moyenne des écarts entre coordonnées uniques triées, 1.0 s'il n'y en a qu'une.
