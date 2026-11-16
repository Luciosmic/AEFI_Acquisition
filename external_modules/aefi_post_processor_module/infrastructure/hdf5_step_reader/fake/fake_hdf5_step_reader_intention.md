---
type: doublure-de-test::solidai-hexagonal
tldr: "Doublure du lecteur d'étapes : étapes en mémoire, mêmes refus que le réel."
code: ["[[external_modules/aefi_post_processor_module/infrastructure/hdf5_step_reader/fake/fake_hdf5_step_reader.py]]"]
cause_de_changement: outil
implements: ["[[external_modules/aefi_post_processor_module/application/field_map_service/field_map_service_intention^^i-step-reader]]"]
double_de: "[[external_modules/aefi_post_processor_module/infrastructure/hdf5_step_reader/hdf5_step_reader_intention]]"
---
# fake_hdf5_step_reader — Intention

## Rationale

Le lecteur réel exige un fichier HDF5. Sans double en mémoire, chaque test du service de carte devrait en écrire un.

## Responsibility

- Garder des étapes en mémoire, par fichier, et refuser fichier et étape absents comme le réel.

## Design

- Passe la suite de contrat de `IStepReader`, comme l'adaptateur réel.
