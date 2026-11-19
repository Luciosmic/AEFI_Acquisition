---
type: adaptateur::solidai-hexagonal
tldr: "Lire les étapes rangées dans un fichier HDF5 d'acquisition."
code: ["[[external_modules/aefi_post_processor_module/infrastructure/hdf5_step_reader/hdf5_step_reader.py]]"]
cause_de_changement: outil
implements: ["[[external_modules/aefi_post_processor_module/application/field_map_service/field_map_service_intention^^i-step-reader]]"]
---
# hdf5_step_reader — Intention

## Rationale

Les étapes écrites par le traitement doivent se relire telles que rangées, sans que la carte connaisse h5py. Sans adaptateur de lecture, le format se lit par des chaînes écrites à la main, qui divergent de celles de l'écriture.

## Responsibility

- Implémenter `IStepReader` : lister les groupes d'étapes d'un fichier, sans le groupe `raw_scan` des points bruts (aucun si le fichier manque ou est illisible), lire une étape (tableau et métadonnées), refuser une étape ou un fichier absents.
- Ne rien décoder : noms de canaux et étendue reviennent comme rangés.

## Design

- Ouvre le fichier en lecture seule à chaque appel ; les noms viennent de `hdf5_step_format`, comme pour l'écrivain.
- Passe la suite de contrat de `IStepReader`, et relit ce que `Hdf5StepWriter` a écrit.
