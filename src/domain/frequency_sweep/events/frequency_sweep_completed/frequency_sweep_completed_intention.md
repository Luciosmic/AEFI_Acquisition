# frequency_sweep_completed — Intention

## Rationale

Seul un balayage complet peut servir de référence ou de fond : un balayage interrompu n'a pas toutes ses fréquences. Ce fait distingue les deux dans le journal des événements.

## Responsibility

- Porter l'id du balayage, son rôle et le nombre de fréquences acquises.

## Design

- Émis une seule fois, par `FrequencySweep`, quand la dernière fréquence de la grille est acquise.
