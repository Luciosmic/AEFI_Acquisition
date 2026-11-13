---
type: atome::solidai-atome
tldr: "Nommer la promesse refusée : « un point de fréquence contient exactement N échantillons »."
code: ["[[src/domain/frequency_sweep/errors/frequency_point_incomplete_error.py]]"]
cause_de_changement: regle-metier
---
# frequency_point_incomplete_error — Intention

## Rationale

Une moyenne sur 3 échantillons au lieu de 50 a une dispersion bien plus grande : comparée à un fond acquis avec 50, elle ferait passer du bruit pour un écart.

## Responsibility

- Nommer la promesse refusée : « un point de fréquence contient exactement N échantillons ».

## Design

- Hérite de `ValueError` (convention `AefiPointIncompleteError`) ; porte l'id du balayage, la fréquence, N attendu et le nombre reçu.
