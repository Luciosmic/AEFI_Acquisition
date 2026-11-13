---
type: port::solidai-hexagonal
tldr: "Port sortant `i_frequency_sweep_output_port` : `present_frequency_sweep_step` : l'étape en cours, en clair."
sens: sortant
code: "[[src/application/frequency_sweep/frequency_sweep_service/ports/i_frequency_sweep_output_port.py]]"
---
# i_frequency_sweep_output_port — Intention

## Rationale

Un balayage au banc dure plusieurs minutes : l'opérateur doit voir chaque fréquence arriver, et non un résultat final après un silence. Le service ne connaît pas Qt.

## Responsibility

- `present_frequency_sweep_step` : l'étape en cours, en clair.
- `present_frequency_point_measured` : une fréquence acquise, pour le tracé en direct.
- `present_frequency_sweep_ended` : fin normale ou arrêt demandé, avec ce qui a été acquis et le dossier d'export.
- `present_frequency_sweep_failed` : refus au démarrage ou échec en cours, avec la raison.

## Design

- Appelé depuis la tâche de fond : l'implémentation doit être sûre entre threads (signaux Qt).
