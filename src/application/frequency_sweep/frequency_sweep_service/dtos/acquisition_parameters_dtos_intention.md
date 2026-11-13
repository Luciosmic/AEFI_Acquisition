---
type: atome::solidai-atome
tldr: "DTO `acquisition_parameters_dtos` : `FrequencySweepActivityDTO` : ce que le balayage a fait (activité PROV) — rôle, grille, N, hauteur de table, délais, contrôles tenus, excitation appliquée, opérateur, origine du flux, positions du banc, latence USB, issue."
code: ["[[src/application/frequency_sweep/frequency_sweep_service/dtos/acquisition_parameters_dtos.py]]"]
cause_de_changement: orchestration
---
# acquisition_parameters_dtos (balayage en fréquence) — Intention

## Rationale

Un fond n'est réutilisable que si l'on sait, après coup, dans quelles conditions il a été acquis. Le service rassemble ces faits ; le format du fichier (`acquisition-parameters.json`) appartient à l'infrastructure.

## Responsibility

- `FrequencySweepActivityDTO` : ce que le balayage a fait (activité PROV) — rôle, grille, N, hauteur de table, délais, contrôles tenus, excitation appliquée, opérateur, origine du flux, positions du banc, latence USB, issue.
- `SweptExcitationDTO` : mode et niveaux de l'opérateur, appliqués à chaque fréquence, et sa fréquence, rétablie à la fin.
- `FrequencySweepAcquisitionParametersDTO` : l'activité, les conditions matérielles, la provenance du code et les fichiers écrits.

## Design

- Calque `acquisition_throughput_characterization_service/dtos/acquisition_parameters_dtos.py` ; les conditions communes viennent de `application/shared/acquisition_parameters/`.
- Primitives seulement, sans format.
