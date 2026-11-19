---
type: doublure-de-test::solidai-hexagonal
tldr: "Doublure de l'écrivain d'étapes : étapes et historique en mémoire, même contrat que le réel."
code: ["[[external_modules/aefi_post_processor_module/infrastructure/hdf5_step_writer/fake/fake_hdf5_step_writer.py]]"]
cause_de_changement: outil
implements: ["[[external_modules/aefi_post_processor_module/application/post_processing_service/post_processing_service_intention^^i-step-writer]]"]
double_de: "[[external_modules/aefi_post_processor_module/infrastructure/hdf5_step_writer/hdf5_step_writer_intention]]"
---
# fake_hdf5_step_writer — Intention

## Rationale

L'adaptateur réel crée un fichier HDF5. Sans double en mémoire, chaque test du service devrait en ouvrir un.

## Responsibility

- Garder les étapes, l'historique, la source consignée et les points bruts en mémoire, refuser une étape jamais rangée comme le réel.

## Design

- Passe la suite de contrat de `IStepWriter`, comme l'adaptateur réel.
