---
type: atome::solidai-atome
tldr: "Placer les points d'un scan sur une grille carrée, NaN là où rien n'a été mesuré, sans dépendre de pandas."
code: ["[[external_modules/aefi_post_processor_module/domain/processing/grid_builder/grid_builder.py]]"]
cause_de_changement: regle-metier
---
# grid_builder — Intention

## Rationale

Un scan interrompu ou rectangulaire ne se superpose pas à un autre : sans grille carrée, chaque étape suivante (calibration, rotation, interpolation) devrait gérer des tailles et des trous différents. Tant que cette mise en grille vivait dans une classe qui lit un `DataFrame` pandas, le domaine ne pouvait pas la porter, et les chiffres de l'extension de la carte (`extent`) dépendaient d'un lecteur de CSV.

## Responsibility

- Rendre une grille `(N, N, canaux)` indexée `[y, x, canal]`, avec `N = max(nx, ny)` ou la taille demandée, NaN où aucun point n'existe.
- Rendre les métadonnées de la grille : `extent` (bords des cellules), coordonnées uniques, pas, nombres de points valides et totaux.
- Refuser un scan sans canal.

## Design

- Fonction `build_square_grid(x, y, values, channel_names, grid_size)` sur des tableaux numpy ; la lecture du CSV et sa conversion en tableaux restent à l'appelant (pandas, hors du domaine).
- Le pas est la moyenne des écarts entre coordonnées uniques triées, 1.0 s'il n'y en a qu'une.
- Résultat identique octet pour octet à l'ancienne boucle ligne à ligne : l'étalon `golden_master_test` le garde.
