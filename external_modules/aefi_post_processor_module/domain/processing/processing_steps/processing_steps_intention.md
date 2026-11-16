---
type: atome::solidai-atome
tldr: "Fixer les noms, l'ordre et les paramètres gelés des cinq étapes du traitement, pour que tous les couches parlent des mêmes."
code: ["[[external_modules/aefi_post_processor_module/domain/processing/processing_steps/processing_steps.py]]"]
cause_de_changement: regle-metier
---
# processing_steps — Intention

## Rationale

Les noms d'étapes étaient des chaînes écrites à la main dans le pipeline, le lecteur de fichiers et la visualisation. Une faute de frappe ne donnait aucune erreur, et l'ordre des étapes n'existait qu'à l'intérieur d'une méthode du pipeline.

## Responsibility

- Nommer les cinq étapes (`preprocessed`, `phase_calibrated`, `amplitude_subtracted`, `rotated_frame`, `interpolated`) et leur ordre, liste fermée.
- Refuser un nom inconnu (`step_index`).
- Porter les paramètres d'un traitement dans un objet gelé : largeur de bord, méthode d'interpolation, taille de grille, point de référence, angles de rotation.

## Design

- Constantes et un tuple `STEP_NAMES` ; `ProcessingParameters` est une `@dataclass(frozen=True)`.
- Les valeurs par défaut sont celles de `ProcessingPipeline`, pour que le service de la tranche 1.4 rejoue le même traitement.
