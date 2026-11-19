---
type: adaptateur::solidai-hexagonal
tldr: "Ranger les étapes calculées dans un fichier HDF5, un groupe par étape."
code: ["[[external_modules/aefi_post_processor_module/infrastructure/hdf5_step_writer/hdf5_step_writer.py]]"]
cause_de_changement: outil
implements: ["[[external_modules/aefi_post_processor_module/application/post_processing_service/post_processing_service_intention^^i-step-writer]]"]
---
# hdf5_step_writer — Intention

## Rationale

Le traitement doit laisser ses étapes, les points bruts relus du CSV et leur provenance dans un fichier HDF5 qui est le sien, au format que la carte relit : l'acquisition n'exporte que le CSV, donc ce fichier n'existe pas avant lui. Sans adaptateur, h5py entre dans le service et le format se dilue en chaînes écrites à la main.

## Responsibility

- Implémenter `IStepWriter` : ouvrir le fichier d'étapes de l'acquisition, le créer s'il n'existe pas, ranger une étape (données compressées, métadonnées typées), garder l'historique dans le fichier.
- Consigner la source en attributs de la racine (CSV, SHA-256 du CSV lu, identifiant de l'activité, empreinte déclarée par l'acquisition, égalité des deux) et ranger les points bruts relus du CSV dans le groupe `raw_scan` (`positions`, `values`, `channel_names`), qui n'est pas une étape.
- Reproduire à l'identique l'écriture de l'ancien `DataHandler` : l'étalon `golden_master_test` le vérifie.

## Design

- Les noms viennent de `hdf5_step_format` ; le chemin du fichier sort de `processing_store_path`.
- Une source consignée de nouveau ne garde rien de la précédente : un attribut absent de la nouvelle est retiré.
- Les listes, tuples et dictionnaires de métadonnées sont écrits en tableau ou en JSON, comme avant.
