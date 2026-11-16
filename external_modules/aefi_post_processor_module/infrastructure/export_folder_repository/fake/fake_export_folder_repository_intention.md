---
type: doublure-de-test::solidai-hexagonal
tldr: "Doublure du dépôt d'acquisitions : acquisitions en mémoire, même ordre que le réel."
code: ["[[external_modules/aefi_post_processor_module/infrastructure/export_folder_repository/fake/fake_export_folder_repository.py]]"]
cause_de_changement: outil
implements: ["[[external_modules/aefi_post_processor_module/domain/acquisition_record/acquisition_record_intention^^i-acquisition-repository]]"]
double_de: "[[external_modules/aefi_post_processor_module/infrastructure/export_folder_repository/export_folder_repository_intention]]"
---
# fake_export_folder_repository — Intention

## Rationale

Le dépôt réel parcourt un dossier et lit des dates de fichiers. Sans double en mémoire, chaque test du catalogue devrait construire un dossier daté.

## Responsibility

- Garder des acquisitions en mémoire, par dossier d'export, triées par nom comme le réel.

## Design

- Passe la suite de contrat de `IAcquisitionRepository`, comme l'adaptateur réel.
