# bench_referential — Intention

## Rationale

Le banc se lit dans deux référentiels : celui des butées (0 à la butée de homing, ce que le contrôleur et le scan connaissent) et le référentiel centré (0,0 au milieu du banc, quatre quadrants). Sans une conversion unique, chaque panneau recopie « raw ± centre » à sa façon, et la zone de scan saisie dans un référentiel est lue dans l'autre : un scan part à 600 mm des butées au lieu de 600 mm du centre, sans qu'aucun message ne le dise.

## Responsibility

- Convertir une coordonnée de l'axe X ou Y entre le référentiel affiché et le référentiel des butées (`to_raw_*`, `to_display_*`).
- Porter le mode (`limit_switch` ou `centered`) et la course des axes en mm, dont la moitié est le centre.

## Design

- Valeur immuable : changer de mode ou de course donne une nouvelle instance (`with_mode`, `with_limits`).
- Aucune dépendance Qt, domaine ou application : le centre est la moitié de la course reçue du service de mouvement, qui la tire de la course en incréments × µm par incrément.
- Le référentiel des butées est canonique : tout ce qui part vers le service, et tout ce qui se persiste, y reste.
