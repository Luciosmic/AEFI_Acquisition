# adc_output_rate_characterization_widget — Intention

## Rationale

L'ODR de l'ADC n'avait été mesurée que par un script autonome, application
fermée. Sans cette section, l'opérateur doit quitter le logiciel pour la
refaire, et ne voit jamais si un OSR choisi dans Hardware Advanced Config est
réellement appliqué par la puce. La grandeur « cadence » du catalogue ADC se
saisissait à la main.

## Responsibility

- Paramètres : voie de l'oscilloscope sur DRDY (1-4), rapport de sonde
  (×10 / ×1), OSR à balayer (pré-remplis par le presenter avec les valeurs
  acceptées par l'ADS131A04), périodes par capture.
- « Mesurer à l'OSR courant » (rien n'est modifié) et « Balayer les OSR » →
  `start_requested(osr_values, channel, probe_ratio, periods)` ; liste
  illisible ou vide refusée dans le panneau.
- Tableau au fil des mesures (OSR, ODR, écart-type des intervalles,
  intervalles réguliers / écartés, f_MOD implicite), courbe ODR(OSR) en
  log-log avec `f_MOD moyenne / OSR`, résumé (f_MOD, écart entre OSR, OSR
  restauré, instrument).

## Design

- Affichage seulement : valeurs calculées dans les DTO ; seule la conversion
  d'unités est faite ici.
- Inséré dans l'onglet ADC par `CalibrationPanel` via
  `HardwareComponentPanel.add_tool()`, comme la mesure de débit dans l'onglet
  Microcontrôleur.
