---
doc_type: constat
---

# Catalogue : un fichier d'étapes sans l'étape `preprocessed` compte « à recalculer »

Décision de la session sur la limite 1 de 1.5 (un traitement échoué laisse un `.h5` vide plus récent que le CSV, l'acquisition apparaît « traitée »).

- **Règle** : `AcquisitionRecord.recalculation_reason` rend `incomplete` quand le fichier d'étapes existe sans l'étape `preprocessed`, avant le recalcul forcé et avant la comparaison des dates. Un fichier absent reste `new`. Le dépôt `ExportFolderRepository` ouvre le fichier en lecture seule pour le savoir (dates inchangées, test « lister ne modifie rien » vert) ; un fichier qui ne s'ouvre pas ne contient aucune étape.
- **Preuve rouge puis verte** : `pytest-catalogue-fichier-vide-rouge.log` (`('processed', None) == ('to_recompute', 'incomplete')` en échec) puis `pytest-catalogue-fichier-vide-vert.log` (31 réussis). Test : `test_a_failed_processing_leaves_a_steps_file_that_the_next_session_still_calls_to_recompute`, qui construit un catalogue neuf pour que l'échec ne vienne pas de la mémoire de session.
- **Limite restante** : un traitement qui échoue après avoir rangé `preprocessed` laisse des étapes partielles que la règle ne voit pas (l'acquisition apparaît « traitée » dans une nouvelle session). Si l'humain veut aussi ce cas : exiger les cinq étapes, ou la dernière attendue selon les angles (sans angles, `rotated_frame` n'existe pas).
- **Ce que cela change pour une vraie acquisition** : l'`.h5` créé par l'acquisition sans étapes post-traitées passe de « traitée » à « à recalculer » (`incomplete`), ce qui est le bon état.
