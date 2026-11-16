---
type: adaptateur::solidai-hexagonal
tldr: "Retrouver les acquisitions d'un dossier d'export et les dates de leur scan et de leurs étapes."
code: ["[[external_modules/aefi_post_processor_module/infrastructure/export_folder_repository/export_folder_repository.py]]"]
cause_de_changement: outil
implements: ["[[external_modules/aefi_post_processor_module/domain/acquisition_record/acquisition_record_intention^^i-acquisition-repository]]"]
---
# export_folder_repository — Intention

## Rationale

Les acquisitions vivent dans des sous-dossiers `<horodatage>_<stepScan|flyScan>_<nom>/` de l'export, avec leur `*_aefi.csv`. Sans adaptateur, le parcours du disque et la lecture des dates entrent dans le catalogue ou dans la règle du domaine.

## Responsibility

- Implémenter `IAcquisitionRepository` : parcourir `*_stepScan_*` et `*_flyScan_*`, trier par nom de dossier, rendre un `AcquisitionRecord` par scan avec la date du CSV et celle du fichier d'étapes (absente s'il n'existe pas).
- Ne rien créer ni modifier.

## Design

- Le fichier d'étapes se déduit du fichier d'acquisition `<dossier>/<nom>.h5` par `processing_store_path`, le même chemin que l'écriture.
- Un dossier d'export absent ne contient aucune acquisition ; un dossier sans `*_aefi.csv` n'est pas une acquisition.
