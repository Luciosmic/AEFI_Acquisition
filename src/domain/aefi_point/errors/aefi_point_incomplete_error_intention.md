# aefi_point_incomplete_error — Intention

## Rationale

Sans erreur nommée, un point à 3 échantillons sur 10 est soit accepté en silence, soit rejeté par un `ValueError` anonyme que l'appelant ne peut pas distinguer d'un bug, ce qui force à parser des messages.

## Responsibility

- Nommer la promesse refusée : « un point contient exactement N échantillons valides ».

## Design

- Hérite de `ValueError` (convention `OperatorNameBlankError`) ; porte l'id du point, N attendu et nombre reçu.
