# narda_point_incomplete_error — Intention

## Rationale

Sans erreur nommée, un point de champ moyenné sur 3 échantillons au lieu de 10, ou une baseline présente hors mode différentiel, est soit accepté en silence, soit rejeté par un `ValueError` anonyme que l'appelant ne peut pas distinguer d'un bug.

## Responsibility

- Nommer la promesse refusée : « un point de champ contient exactement N échantillons (et N de baseline si le mode différentiel l'exige, aucun sinon) ».

## Design

- Hérite de `ValueError` ; porte l'id du point, N attendu, nombre reçu et `what` (`samples` ou `baseline samples`) pour distinguer la fenêtre fautive.
