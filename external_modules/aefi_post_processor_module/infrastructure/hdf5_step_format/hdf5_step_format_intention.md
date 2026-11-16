---
type: atome::solidai-atome
tldr: "Dire en un seul endroit comment les étapes calculées sont rangées dans un fichier HDF5 et où vit le fichier d'étapes d'une acquisition."
code: ["[[external_modules/aefi_post_processor_module/infrastructure/hdf5_step_format/hdf5_step_format.py]]"]
cause_de_changement: outil
---
# hdf5_step_format — Intention

## Rationale

L'écriture des étapes et leur lecture par la carte reposent sur les mêmes noms de groupes et d'attributs. Écrits à la main des deux côtés, ils divergent au premier renommage et la carte ne trouve plus ce que le traitement a écrit. Le fichier d'étapes lui-même va changer de place (un fichier propre au post-traitement, tranche 6) : si chaque adaptateur calcule ce chemin, il faut les trouver tous.

## Responsibility

- Nommer le groupe d'une étape, son jeu de données et les attributs d'un groupe et de la racine.
- Donner le chemin du fichier d'étapes d'une acquisition, `processing_store_path`.

## Design

- Constantes et deux fonctions pures, sans h5py : le format est un vocabulaire, les adaptateurs ouvrent les fichiers.
- `processing_store_path` rend aujourd'hui le fichier de l'acquisition : l'acquisition lance le traitement sur son propre `.h5`. Le passage à un fichier séparé change cette seule fonction.
