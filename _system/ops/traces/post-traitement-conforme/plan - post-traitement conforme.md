# Plan — Post-traitement conforme à l'acquisition

**État :** tranche 1 (conformité de base) faite et fusionnée dans `develop` le 2026-11-16 (`c25ef87c`, `dev_post_processor` conservée) : couches DDD, fenêtre à panneaux Acquisitions, Carte et Logs, lancement qui ne calcule plus, étalon `golden_master_test` inchangé. Vérifiée : V1 = 132 réussis et les 2 échecs connus (180° sur x et y), V2 = 0 erreur, V3 = 8 réussis. À confirmer sur le PC du laboratoire : l'ouverture sur les vraies acquisitions, sans qu'aucun fichier ne change, et un « Traiter » (l'humain n'a vu la fenêtre que sur une copie de données synthétiques).
**Sur le PC du laboratoire, le 2026-11-16 :** la fenêtre s'est ouverte sur les 10 vraies acquisitions sans écrire de fichier. Le scan rectangulaire de la bouteille d'eau (150 × 100 points) s'affichait avec 50 lignes vides en haut, car toute grille était complétée en carré. Corrigé hors tranches, à la demande de l'humain (branche `fix/post-traitement-grille-rectangulaire`) : la grille suit celle que l'acquisition a prévue, lue dans `<acquisition>_acquisition-parameters.json` par le port `IScanPlanReader` (adaptateur `acquisition_parameters_scan_plan_reader`), et l'interpolation en garde les proportions ; un scan interrompu garde ses lignes prévues vides, et un scan sans description (dont ceux de l'étalon) garde la grille carrée, aux chiffres identiques. La tranche 2 prolonge ce lecteur pour l'objet et les angles, derrière le même port. Sur ce PC, l'étalon et les 2 tests de 180° échouent déjà sur `develop` sans la correction : l'étalon fait sur le Mac ne s'y reproduit pas à l'identique ; la correction a été vérifiée en comparant, sur ce PC, les sorties avant et après (identiques).
**Décisions de l'humain, 2026-11-16 :** le fichier des paramètres d'acquisition est un contrat entre les deux logiciels, en relation **client-fournisseur** (le post-traitement client, l'acquisition fournisseur) : un besoin du post-traitement peut faire évoluer l'acquisition. Cela remplace, pour ce fichier, le conformisme de la conception (§ 1.1). Les deux écarts relevés par la carte des contextes (`_system/documentation/context-map-acquisition-post-traitement.md`, § 6) se corrigent en tranche 2 : les angles appliqués lus dans l'export au lieu des angles idéaux, et l'empreinte du `.h5` que le traitement rend fausse. Pour l'empreinte, décidé par l'humain : l'acquisition n'exporte plus que des CSV (source brute unique), et le post-traitement crée le `.h5`, où il regroupe les données brutes relues des CSV, ses cinq étapes et leur provenance (CSV source, son SHA-256, `provenance.activity.id`). Premier besoin du client envers l'acquisition : retirer `Hdf5ScanExportPort` du service d'export, déclencher le traitement sur le seul CSV, relever la version mineure du schéma (`data.files` sans `.h5`). À revérifier au codage : les attributs de configuration du `.h5` actuel sont tous dans le fichier des paramètres (détail : carte des contextes, § 6).
**Prochaine action :** tranche 2 (lecture des paramètres d'acquisition : objet, angles réellement appliqués à la place des angles idéaux, `RotationConvention` empruntée). Même méthode que la tranche 1 : découpage en étapes avec test d'acceptation, un commit par étape, étalon à ne changer que par une décision sur les chiffres. À proposer à l'humain, hors des tranches 1 à 6 validées : « Traiter en tâche de fond » (le bouton « Traiter » fige la fenêtre pendant le calcul, comme l'ancien traitement au lancement ; un thread ou un processus avec progression, sans changer les résultats).

## Pourquoi

Le module `external_modules/aefi_post_processor_module/` n'a pas suivi le logiciel d'acquisition.
Il ignore le référentiel centré, n'a pas de profils, retraite par lot avec les angles idéaux du capteur alors que chaque export porte les angles appliqués, et n'avait aucun journal lisible.
On le remet au niveau de l'acquisition : même fenêtre à panneaux, mêmes couches DDD, et une relation conformiste à l'acquisition, décrite objet par objet.

## Périmètre

- `external_modules/aefi_post_processor_module/` en entier.
- Une seule tranche touche `src/` : l'adaptateur `src/infrastructure/post_processing/aefi_post_processor_port.py`, quand il passera par le service du post-traitement.
- Rien d'autre de l'acquisition n'est modifié : elle est l'amont, le post-traitement s'y conforme.

## Étapes

1. Journal du post-traitement lisible hors de sa fenêtre, bilan du traitement par lot, cadre System Feedback branché dessus — **fait**.
2. Conception de l'architecture en panneaux et récits utilisateurs — **à valider**.
3. Tranches 1 à 6 de la conception, chacune vérifiée par l'humain. Tranche 1 **faite** (traces `2026-11-16-tranche-1-etapes-*`) ; tranches 2 à 6 à faire.

## Constats à ne pas perdre

- Deux tests de calcul échouent depuis avant ce plan : la calibration de phase (écart de 180° sur deux axes) et la soustraction d'amplitude. Tranche 5.
- Un retraitement par lot remplace, dans le `.h5`, les angles de la calibration active par les angles idéaux. Tranche 2.
