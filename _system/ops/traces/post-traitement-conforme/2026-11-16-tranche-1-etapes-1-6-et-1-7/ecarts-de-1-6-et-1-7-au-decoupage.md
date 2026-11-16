---
doc_type: constat
---

# Étapes 1.6 et 1.7 : ce qui s'écarte du découpage, et pourquoi

Écritures faites avec les outils natifs (le gate `au` de la session parente n'a pas été utilisé). Typage `constat::sh-agent-os` non fait : à la charge de la session.

## Écarts

1. **La nouvelle fenêtre est le défaut dès 1.6.** Le test de lancement lance `composition_root.py --repo-path` et attend `window.shown` : la fenêtre ouverte est donc la nouvelle. L'ancienne restait lançable par `visualisation/composition_root_visualisation.py` entre les deux commits, puis a été supprimée en 1.7.
2. **Deux options de plus sur `composition_root.py`** : `--log-file` et `--layout-file`. Sans elles, le test de lancement écrirait dans le journal et la disposition réels. Défauts : ceux d'avant pour le journal, `~/.aefi_post_processor_layout.dat` pour la disposition (jamais `~/.aefi_acquisition_layout.dat`).
3. **L'intention du paquet `aefi_acquisition_upstream` ne déclare pas de cause de changement.** A15 range `outil` sous `infrastructure/` ou `interface/` et le paquet est hors des quatre couches : avec la cause, V2 donne 1 erreur. Sans elle, 0. À signaler à SOLIDAI avec les deux règles manquantes déjà notées (sens des dépendances d'un paquet d'emprunt, unicité des noms entre deux arbres de couches).
4. **`logs_presenter` est un `atome`, pas un `presenter`** : le type `presenter` exige `appelle` (au moins un port entrant) et les Logs n'appellent aucun service. `acquisitions_presenter` et `field_map_presenter` sont des `presenter`.
5. **`shell_wiring` est un `atome` (outil)**, pas un `point-de-composition` : il ne construit aucun adaptateur (il appelle `headless_wiring`), donc n'a rien à mettre dans `cable`.
6. **Les deux tests d'origine de `sync_scans` (`observability_test.py`) sont remplacés** par leurs équivalents sur le presenter (mêmes messages : `scan.processing ... rotation_origin=ideal_template`, `scan.failed ... error_type=ValueError`, `scan.up_to_date`, `sync.finished` en avertissement avec `processed=1 skipped=1 failed=1`). Le cas « dossier absent » (erreur `sync.aborted`) devient l'avertissement `acquisitions.none_found` : le catalogue rend une liste vide pour un dossier absent, il ne distingue pas l'absence du vide. Les noms des tests d'origine changent donc dans V1.
7. **`processing/datahandler.py` supprimé** avec `visualisation/` : son dernier lecteur était `visualisation/model.py`. L'export `DataHandler` de `processing/__init__.py` part avec.
8. **`FieldMapDTO` gagne `metadata`** (rotation et point de référence stockés avec l'étape) : l'ancienne fenêtre les affichait (« Frame Info »).
9. **Le service pose `processing_step` sur l'exception qu'il relance**, sans changer son type : c'est ainsi que le bilan nomme l'étape fautive, sans toucher au comportement vu par l'adaptateur de `src/`.
10. **La comparaison avec l'ancien modèle de la carte (1.5) devient une comparaison avec la lecture directe du fichier par h5py**, l'ancien modèle étant supprimé.

## Limites constatées, à décider

- **Le traitement est synchrone sur le fil de la fenêtre** (comme l'ancien traitement au lancement) : le bouton « Traiter » fige la fenêtre pendant le calcul. Passer en tâche de fond est un changement de comportement, hors tranche 1.
- **Le bouton « tout ce qui est à recalculer » ne reprend pas les acquisitions en échec** de la session ; pour les réessayer, on les sélectionne et on utilise « Traiter la sélection ».
- **La disposition par défaut met les trois panneaux en onglets** (celle de l'acquisition) ; l'humain les déplace, et sa disposition est gardée à la fermeture.
