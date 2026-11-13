# frequency_not_in_grid_error — Intention

## Rationale

Un point acquis à une fréquence hors de la grille rendrait le balayage incomparable aux autres sur la même grille, sans que rien ne le signale.

## Responsibility

- Nommer la promesse refusée : « un balayage ne contient que des fréquences de sa grille ».

## Design

- Hérite de `ValueError` (convention `AefiPointIncompleteError`) ; porte l'id du balayage et la fréquence refusée.
