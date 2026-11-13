# column_stabilization_record — Intention

## Rationale

Quand un scan attend le repos de la colonne sur l'accéléromètre, la mesure de chaque point dépend de ce que l'accéléromètre a vu.
Sans l'exporter, on ne peut ni vérifier après coup que la colonne était au repos, ni retrouver les points mesurés au délai maximal ou au délai fixe.

## Responsibility

- Tenir, pour un scan exporté, le niveau de repos (`ColumnRestMeasured`) et le décompte des attentes (`ColumnSettled`) par façon dont elles se sont terminées.
- Rendre une ligne de la table `column-stabilization` par attente, quand les points sont jugés sur l'accéléromètre.
- Rendre une ligne de la table `accelerometer` par échantillon reçu pendant le scan, datée sur l'horloge de l'hôte.
- Rendre le résumé écrit dans le fichier de paramètres (`procedure.step_scan.column_stabilization`).

## Design

- Pas d'entrée-sortie : le service d'export ouvre les tables et y écrit les lignes rendues ici.
- L'accéléromètre s'enregistre pendant tout le scan dès qu'il émet, mesure du repos comprise, qu'il serve ou non à juger les points : ce sont les données qui permettent de vérifier le jugement.
- La table `column-stabilization` ne s'écrit que si les points sont jugés sur l'accéléromètre ; au délai fixe partout, le résumé suffit.
- Les échantillons portent l'instant de réception sur une horloge monotone ; une même origine prise au démarrage du scan sur les deux horloges les date.
- Les faits d'un autre scan (`scan_id` différent) sont ignorés.
