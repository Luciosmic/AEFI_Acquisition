---
type: evenement-de-domaine::solidai-ddd
tldr: "Porter l'id du balayage, son rôle et le nombre de fréquences acquises."
code: ["[[src/domain/frequency_sweep/events/frequency_sweep_completed/frequency_sweep_completed.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/frequency_sweep/frequency_sweep_intention]]"
---
# frequency_sweep_completed — Intention

## Rationale

Seul un balayage complet peut servir de référence ou de fond : un balayage interrompu n'a pas toutes ses fréquences. Ce fait distingue les deux dans le journal des événements.

## Responsibility

- Porter l'id du balayage, son rôle et le nombre de fréquences acquises.

## Design

- Émis une seule fois, par `FrequencySweep`, quand la dernière fréquence de la grille est acquise.
