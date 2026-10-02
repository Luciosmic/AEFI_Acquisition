# acquisition_throughput_characterization_widget — Intention

## Rationale

La grandeur « Débit d'acquisition optimal vs n_avg » du microcontrôleur se
saisissait à la main, à partir d'une mesure faite ailleurs (et perdue). Sans
cette section, l'opérateur doit fermer l'application pour mesurer, puis
recopier des chiffres — et ne voit jamais la courbe qui justifie le choix de
`n_avg`.

## Responsibility

- Grille de `n_avg` (texte : entiers séparés par virgules/espaces) et
  échantillons par point, pré-remplis par le presenter avec la requête par
  défaut ; une grille illisible est refusée dans le panneau. Ajouté le
  2026-10-02 : sur le banc, le bruit est dominé par le 50 Hz secteur et il faut
  mesurer aux zéros du moyennage (multiples de 20 à OSR 4096), absents de la
  grille par défaut ; l'infobulle le rappelle.
- Bouton « Mesurer débit et bruit vs n_avg (excitation coupée) » →
  `start_requested(n_avg_values, samples_per_point)`, désactivé (avec la
  grille) pendant le balayage.
- Tableau rempli au fil des points : `n_avg`, période (ms), débit, conversions
  ADC/s, σ (µV), bruit en 1 s (µV).
- Deux courbes en fonction de `n_avg` (échelle log2) : débit, et bruit en 1 s ;
  ligne verticale au `n_avg` recommandé.
- Résumé : `n_avg` recommandé, `T₀`, `ODR`, écart au modèle, OSR, excitation ;
  rappel que les débits sont pré-remplis dans le formulaire de caractérisation.

## Design

- Affichage seulement : toutes les valeurs arrivent calculées dans les DTO
  (SI) ; seule la conversion d'unités (ms, µV) est faite ici.
- Inséré dans l'onglet Microcontrôleur par `CalibrationPanel` via
  `HardwareComponentPanel.add_tool()`.
- matplotlib (même rendu sombre que l'onglet Géométrie source).
