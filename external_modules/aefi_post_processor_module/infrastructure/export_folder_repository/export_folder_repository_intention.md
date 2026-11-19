---
type: adaptateur::solidai-hexagonal
tldr: "Retrouver les acquisitions d'un dossier d'export et les dates de leur scan et de leurs étapes."
code: ["[[external_modules/aefi_post_processor_module/infrastructure/export_folder_repository/export_folder_repository.py]]"]
cause_de_changement: outil
implements: ["[[external_modules/aefi_post_processor_module/domain/acquisition_record/acquisition_record_intention^^i-acquisition-repository]]"]
---
# export_folder_repository — Intention

## Rationale

Les acquisitions vivent dans des dossiers de l'export, avec leur `*_aefi.csv` et leur fichier de paramètres, et l'opérateur les range dans des sous-dossiers par catégorie (`WATER/`, `METALLIC/`…). Un catalogue qui ne lit que le premier niveau perd toute acquisition rangée. Le nom d'un dossier se renomme à la main et n'a pas de version : ce que l'acquisition est se lit dans son fichier de paramètres, le contrat entre les deux logiciels. Sans adaptateur, le parcours du disque, la lecture des dates et celle du contrat entrent dans le catalogue ou dans la règle du domaine.

## Responsibility

- Implémenter `IAcquisitionRepository` : trouver à toute profondeur chaque dossier qui tient un `*_aefi.csv`, trier par nom de dossier, rendre un `AcquisitionRecord` par scan avec la date du CSV, celle du fichier d'étapes (absente s'il n'existe pas), si ce fichier contient l'étape `preprocessed`, le dossier parent relatif à l'export (`group`), et ce que dit le fichier de paramètres (type, date de début, objet mesuré, lift-off, version du schéma, rotation appliquée ou raison de son refus), par le traducteur `acl/acquisition_parameters_translator`.
- Le type vient du contrat. Repli sur le nom du dossier (`_stepScan_`, `_flyScan_`), logué `catalog.kind_from_name`, dans deux cas seulement : pas de fichier de paramètres lisible, ou un `step_scan` déclaré avant le schéma 1.4, où un scan au vol était aussi déclaré `step_scan`.
- Ne pas lister une activité que le contrat ne déclare pas comme scan (série temporelle, balayage en fréquence), ni un dossier dont ni le contrat ni le nom ne disent le type.
- Journaliser en avertissement une rotation que le contrat décrit mais que le traducteur refuse (`catalog.rotation_refused scan=… reason=…`) : l'acquisition reste listée, sans angles appliqués.
- Ne rien créer ni modifier.

## Design

- Le fichier d'étapes se déduit du fichier d'acquisition `<dossier>/<nom>.h5` par `processing_store_path`, le même chemin que l'écriture.
- Le fichier d'étapes s'ouvre en lecture seule pour chercher le groupe `preprocessed` (date inchangée) ; un fichier qui ne s'ouvre pas ne contient aucune étape.
- Un dossier d'export absent ne contient aucune acquisition ; un dossier sans `*_aefi.csv` n'est pas une acquisition.
