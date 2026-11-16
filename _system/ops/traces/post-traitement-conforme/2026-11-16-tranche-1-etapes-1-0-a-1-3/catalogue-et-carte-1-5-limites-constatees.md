---
doc_type: constat
type: constat::sh-agent-os
genere_par: "[[tache - tranche 1 etapes 1 0 a 1 3]]"
---

# Étape 1.5 : ce que le catalogue et la carte font, et deux limites constatées

Test d'acceptation : `_tests/acquisition_catalog_and_field_map_test.py` (adaptateurs réels, dossier d'export temporaire fait des CSV synthétiques).
- « à recalculer » (`new`) pour trois acquisitions sans fichier d'étapes ; « traitée » après le traitement par le service ; « à recalculer » (`source_newer`) quand le CSV est retouché plus tard ; « en échec » avec le message `No voltage columns found in DataFrame` pour un CSV coupé dans son en-tête.
- Lister, avec ou sans `force`, laisse la liste des fichiers et leurs dates identiques.
- Les cinq étapes d'une acquisition traitée donnent les mêmes grilles (NaN égaux) et la même étendue que `VisualisationModel.get_step_data`.

## Limite 1 : un traitement échoué laisse un fichier d'étapes vide

Le lecteur de CSV échoue après l'ouverture du `.h5` (comme l'ancien `DataHandler`, qui l'ouvrait à la construction). Après un échec, le fichier existe et est plus récent que le CSV : la règle « à recalculer » le dit « traité » dès qu'on relance la fenêtre, car l'échec ne vit qu'en mémoire pour la session. Même défaut qu'avant dans `sync_scans` (un `.h5` présent et plus récent faisait sauter l'acquisition).
Correction possible, hors périmètre de 1.5 : ouvrir le fichier au premier `save_step` plutôt qu'à la construction, ou compter comme « à recalculer » un fichier sans l'étape `preprocessed`. À trancher avec le panneau Acquisitions (1.7).

## Limite 2 : le refus d'une convention de rotation non appliquée attend la tranche 2

L'écart 7 demande aussi ce refus dans la racine ; sans convention de rotation dans le module, il n'y a rien à refuser. Noté dans l'intention de `acquisition_record`.

## Choix

- La carte liste les étapes dans l'ordre du traitement (l'ancien modèle suivait l'ordre alphabétique de h5py).
- Adaptateurs à plat : `infrastructure/export_folder_repository/` et `infrastructure/hdf5_step_reader/` (voir `adaptateurs-a-plat-sous-infrastructure-et-raccord-reduit.md`).
