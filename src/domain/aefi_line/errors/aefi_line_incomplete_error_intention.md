# aefi_line_incomplete_error — Intention

## Rationale

Sans erreur nommée, une ligne de fly-scan avec des trous (points non projetés) serait acceptée en silence ou rejetée par un `ValueError` anonyme, ce qui signifie une carte avec des lignes trouées sans trace, ce qui force à auditer chaque carte après coup.

## Responsibility

- Nommer la promesse refusée : « une ligne contient tous ses points de grille, une fois chacun » ; porte l'id, le nombre attendu, les indices manquants et le nombre reçu.

## Design

- Hérite de `ValueError`, comme `AefiPointIncompleteError`.
