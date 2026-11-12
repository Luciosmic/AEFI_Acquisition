# collapsible_section — Intention

## Rationale

Un onglet de réglage qui porte aussi sa documentation (procédure, convention, mise en garde) finit surchargé : les champs que l'opérateur manipule sont noyés sous des paragraphes qu'il ne relit qu'une fois. Sans section repliable, le choix est entre cacher la documentation (elle n'est plus trouvée) et l'étaler (elle gêne le réglage).

## Responsibility

- Afficher un titre explicite, toujours visible, qui dit ce que contient la section.
- Déplier / replier le contenu au clic sur le titre ; replié par défaut.

## Design

- Un `QToolButton` à flèche (titre) au-dessus d'un `QWidget` de contenu dont on bascule la visibilité.
- Le contenu est fourni par l'appelant (`set_content_widget`) ; la section ne sait rien de ce qu'elle contient.
- Pas d'animation, pas d'état persisté : un repli est une commodité de lecture, pas un réglage.
