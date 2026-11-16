---
type: adaptateur::solidai-hexagonal
tldr: "Ranger les étapes calculées dans un fichier HDF5, un groupe par étape."
code: ["[[external_modules/aefi_post_processor_module/infrastructure/hdf5_step_writer/hdf5_step_writer.py]]"]
cause_de_changement: outil
implements: ["[[external_modules/aefi_post_processor_module/application/post_processing_service/post_processing_service_intention^^i-step-writer]]"]
---
# hdf5_step_writer — Intention

## Rationale

Le traitement doit laisser ses étapes dans le fichier de l'acquisition, au format que la carte relit. Sans adaptateur, h5py entre dans le service et le format se dilue en chaînes écrites à la main.

## Responsibility

- Implémenter `IStepWriter` : ouvrir le fichier d'étapes de l'acquisition, ranger une étape (données compressées, métadonnées typées), garder l'historique dans le fichier.
- Reproduire à l'identique l'écriture de l'ancien `DataHandler` : l'étalon `golden_master_test` le vérifie.

## Design

- Les noms viennent de `hdf5_step_format` ; le chemin du fichier sort de `processing_store_path`.
- Les listes, tuples et dictionnaires de métadonnées sont écrits en tableau ou en JSON, comme avant.
