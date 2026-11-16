---
type: presenter::solidai-hexagonal
tldr: "Décider ce que le panneau Carte montre : les étapes de l'acquisition choisie, la carte de l'étape choisie, ses angles de rotation et la valeur sous la souris, sans Qt ni domaine."
code: ["[[external_modules/aefi_post_processor_module/interface/field_map_presenter/field_map_presenter.py]]"]
cause_de_changement: outil
appelle: ["[[external_modules/aefi_post_processor_module/application/field_map_service/field_map_service_intention^^i-api-field-map-service]]"]
vues: ["[[external_modules/aefi_post_processor_module/interface/field_map_panel/field_map_panel.py]]"]
---
# field_map_presenter — Intention

## Rationale

Une étape calculée n'a de sens que dessinée : l'opérateur veut choisir une acquisition, puis une étape, et lire la carte. Si le panneau lisait le fichier d'étapes, décidait de l'ordre des étapes et refaisait la lecture à chaque clic, sa logique ne se testerait qu'avec une fenêtre ouverte, et il connaîtrait le format du stockage.

## Responsibility

- Quand une acquisition est choisie : lister ses étapes dans l'ordre du traitement, numérotées, sans rien dessiner avant que l'opérateur en choisisse une.
- Quand une étape est choisie : charger la carte par `IApiFieldMapService`, la dessiner par `FigureFactory`, afficher les angles de rotation et le point de référence stockés avec l'étape.
- Garder en mémoire les cartes déjà lues, jusqu'à ce que l'acquisition soit retraitée (`refresh`).
- Dire la valeur et la position sous la souris (`Cursor: x=… | z=…`).
- Un échec de lecture d'une étape est noté dans le journal et laisse la carte précédente.

## Design

- Classe Python sans Qt, ni domaine, ni infrastructure ; elle ne connaît de la vue que `set_steps`, `clear_map`, `select_step`, `show_figure(Figure)`, `set_frame_info`, `set_cursor_text` et les signaux `step_selected` et `cursor_moved` (l'événement de souris matplotlib). Les tests la branchent sur une vue Fake et un tracé Fake.
- Le tracé garde `FigureFactory` en tranche 1 ; il passera au panneau emprunté en tranche 4.
- La vue est `interface/field_map_panel/field_map_panel.py`, humble : ni type ni intention (A1), ses tests sont ceux de ce presenter.
