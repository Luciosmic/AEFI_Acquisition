# frequency_already_acquired_error — Intention

## Rationale

Un second enregistrement à la même fréquence écraserait le premier en silence : la réponse exportée ne serait plus celle qui a été présentée en direct.

## Responsibility

- Nommer la promesse refusée : « chaque fréquence de la grille est acquise une seule fois ».

## Design

- Hérite de `ValueError` (convention `AefiPointAlreadyAcquiredError`) ; porte l'id du balayage et la fréquence.
