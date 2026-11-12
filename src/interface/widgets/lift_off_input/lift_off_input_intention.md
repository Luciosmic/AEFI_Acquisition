# lift_off_input — Intention

## Rationale

Le lift-off (distance entre le point le plus bas des sphères et le point le plus
haut de l'objet mesuré) change d'un objet à l'autre et pèse sur tout le champ
mesuré. Sans champ dédié, il finit dans la description libre de l'objet
(« 8 mm des sphères ») : une phrase qu'aucun script d'analyse ne lit, avec une
unité devinée. Deux panneaux le saisissent (Scan, Continuous Reading) : un champ
par panneau ferait deux validations et deux lectures du texte, qui divergeraient
(virgule acceptée ici, refusée là).

## Responsibility

- Saisir le lift-off en mm, positif ou nul, virgule ou point décimal.
- `lift_off_mm()` : la valeur (`float`) ou `None` quand le champ est vide —
  jamais une valeur devinée.
- Dire, au survol, le nom explicite de la grandeur et où elle est écrite.

## Design

- `QLineEdit` avec un validateur d'expression régulière (chiffres, un seul
  séparateur décimal) : un `QDoubleValidator` suit la locale et laisserait
  passer une virgule que `float()` refuse.
- Le nom long vient du schéma (`feature_of_interest` de
  `acquisition-parameters.json` 1.2) ; l'interface dit « Lift-off », plus court.
- Non sauvegardé entre deux sessions, comme l'objet mesuré : il décrit l'objet
  posé maintenant.
