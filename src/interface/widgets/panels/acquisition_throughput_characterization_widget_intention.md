# acquisition_throughput_characterization_widget — Intention

## Rationale

La grandeur « Débit d'acquisition optimal vs n_avg » du microcontrôleur se
saisissait à la main, à partir d'une mesure faite ailleurs (et perdue). Sans
cette section, l'opérateur doit fermer l'application pour mesurer, puis
recopier des chiffres — et ne voit jamais la courbe qui justifie le choix de
`n_avg`.

## Responsibility

- Bouton « Mesurer débit et bruit vs n_avg (excitation coupée) » →
  `start_requested`, désactivé pendant le balayage.
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
