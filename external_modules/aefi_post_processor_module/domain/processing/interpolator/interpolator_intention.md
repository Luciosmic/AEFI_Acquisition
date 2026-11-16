---
type: atome::solidai-atome
tldr: "Rééchantillonner la carte sur une grille plus fine pour l'affichage et la comparaison, sans inventer de zone non mesurée."
code: ["[[external_modules/aefi_post_processor_module/domain/processing/interpolator/interpolator.py]]"]
cause_de_changement: regle-metier
---
# interpolator — Intention

## Rationale

La carte mesurée est grossière et trouée aux bords d'un scan incomplet. Sans interpolation, l'affichage est en blocs et deux cartes de pas différents ne se comparent pas ; avec une interpolation naïve, on remplit des zones que personne n'a mesurées.

## Responsibility

- Construire une grille cible plus fine sur la même étendue, aux proportions de la grille d'origine : un scan rectangulaire donne une grille fine rectangulaire, un scan carré la même grille qu'avant.
- Interpoler chaque canal avec la méthode demandée (cubique par défaut), en gardant NaN hors de la zone mesurée.
- Rendre le champ interpolé et ses métadonnées (taille, méthode, étendue).

## Design

- Classe `DataInterpolator` (scipy `griddata` et `RectBivariateSpline`).
- La méthode et la taille cible sont des paramètres de `ProcessingParameters`.
