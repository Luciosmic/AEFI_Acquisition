# export_comment_input — Intention

## Rationale

La « base » libre du nom de fichier servait aussi à noter une circonstance (`_background`, une fréquence, une sonde).
Le nom vient désormais de l'objet mesuré et du lift-off ; une circonstance doit pouvoir s'écrire quand même, sans retomber dans le nom.

## Responsibility

- Saisir un commentaire libre au démarrage d'une acquisition (panneaux Scan et Continuous Reading).
- Le rendre sans espaces de bord ; vide = pas de commentaire.

## Design

- Le commentaire part dans `provenance.activity.operator_comment` du fichier de paramètres, jamais dans un nom de fichier ; l'infobulle le dit à l'opérateur.
- Gardé pour la session, jamais enregistré dans les réglages par défaut : un commentaire décrit une acquisition, pas la suivante.
- Un seul widget pour les deux panneaux, comme `LiftOffInput`, pour un même libellé et une même infobulle.
