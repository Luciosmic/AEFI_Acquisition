---
type: plan-de-travail::sh-agent-os
etapes:
  - ^: etape-1-0
    titre: "Préparation : worktree et relevés V1, V2, V3 (tranche 1)"
  - ^: etape-1-1
    titre: "Étalon de non-régression, ou golden master (tranche 1)"
    precedee_par: "[[plan - post-traitement conforme^^etape-1-0]]"
  - ^: etape-1-2
    titre: "Rangement hors des couches (tranche 1)"
    precedee_par: "[[plan - post-traitement conforme^^etape-1-1]]"
  - ^: etape-1-3
    titre: "Le domaine (tranche 1)"
    precedee_par: "[[plan - post-traitement conforme^^etape-1-2]]"
  - ^: etape-1-4
    titre: "Le service de traitement, son lecteur de CSV et son écrivain d'étapes (tranche 1)"
    precedee_par: "[[plan - post-traitement conforme^^etape-1-3]]"
  - ^: etape-1-5
    titre: "Le catalogue des acquisitions et la lecture d'une carte (tranche 1)"
    precedee_par: "[[plan - post-traitement conforme^^etape-1-4]]"
  - ^: etape-1-6
    titre: "La coquille : emprunt, fenêtre à panneaux, journal (tranche 1)"
    precedee_par: "[[plan - post-traitement conforme^^etape-1-5]]"
  - ^: etape-1-7
    titre: "Panneaux Acquisitions et Carte, retrait de l'ancienne fenêtre (tranche 1)"
    precedee_par: "[[plan - post-traitement conforme^^etape-1-6]]"
  - ^: etape-1-8
    titre: "Le lancement ne calcule plus (tranche 1)"
    precedee_par: "[[plan - post-traitement conforme^^etape-1-7]]"
  - ^: etape-1-9
    titre: "Documents, vérification d'ensemble, fusion dans develop (tranche 1)"
    precedee_par: "[[plan - post-traitement conforme^^etape-1-8]]"
  - ^: etape-2-0
    titre: "Préparation : relevés V1, V2, V3 et découpage (tranche 2, partie 1)"
    precedee_par: "[[plan - post-traitement conforme^^etape-1-9]]"
  - ^: etape-2-1
    titre: "Le domaine : la rotation appliquée et les champs de l'acquisition (tranche 2, partie 1)"
    precedee_par: "[[plan - post-traitement conforme^^etape-2-0]]"
  - ^: etape-2-2
    titre: "Le traducteur lit rotation_applied et emprunte RotationConvention (tranche 2, partie 1)"
    precedee_par: "[[plan - post-traitement conforme^^etape-2-1]]"
  - ^: etape-2-3
    titre: "Le catalogue porte la rotation, la version et le refus (tranche 2, partie 1)"
    precedee_par: "[[plan - post-traitement conforme^^etape-2-2]]"
  - ^: etape-2-4
    titre: "Le retraitement utilise les angles appliqués (tranche 2, partie 1)"
    precedee_par: "[[plan - post-traitement conforme^^etape-2-3]]"
  - ^: etape-2-5
    titre: "Le panneau Paramètres d'acquisition : presenter et vue humble (tranche 2, partie 1)"
    precedee_par: "[[plan - post-traitement conforme^^etape-2-4]]"
  - ^: etape-2-6
    titre: "Le panneau dans la fenêtre à panneaux (tranche 2, partie 1)"
    precedee_par: "[[plan - post-traitement conforme^^etape-2-5]]"
  - ^: etape-2-7
    titre: "Documents, vérification d'ensemble et capture du panneau (tranche 2, partie 1)"
    precedee_par: "[[plan - post-traitement conforme^^etape-2-6]]"
  - ^: etape-2-8
    titre: "Retirer Hdf5ScanExportPort de l'export de l'acquisition (tranche 2, partie 2)"
    precedee_par: "[[plan - post-traitement conforme^^etape-2-7]]"
  - ^: etape-2-9
    titre: "Le post-traitement crée le .h5 : données brutes, cinq étapes, provenance (tranche 2, partie 2)"
    precedee_par: "[[plan - post-traitement conforme^^etape-2-8]]"
  - ^: etape-2-10
    titre: "Relever la version mineure du schéma des paramètres (tranche 2, partie 2)"
    precedee_par: "[[plan - post-traitement conforme^^etape-2-9]]"
  - ^: etape-2-11
    titre: "Documents et vérification d'ensemble de la tranche 2 (tranche 2, partie 2)"
    precedee_par: "[[plan - post-traitement conforme^^etape-2-10]]"
---

# Plan — Post-traitement conforme à l'acquisition

**État :** tranche 1 (conformité de base) faite et fusionnée dans `develop` le 2026-11-16 (`c25ef87c`, `dev_post_processor` conservée) : couches DDD, fenêtre à panneaux Acquisitions, Carte et Logs, lancement qui ne calcule plus, étalon `golden_master_test` inchangé. Vérifiée : V1 = 132 réussis et les 2 échecs connus (180° sur x et y), V2 = 0 erreur, V3 = 8 réussis. À confirmer sur le PC du laboratoire : l'ouverture sur les vraies acquisitions, sans qu'aucun fichier ne change, et un « Traiter » (l'humain n'a vu la fenêtre que sur une copie de données synthétiques).
**Sur le PC du laboratoire, le 2026-11-16 :** la fenêtre s'est ouverte sur les 10 vraies acquisitions sans écrire de fichier. Le scan rectangulaire de la bouteille d'eau (150 × 100 points) s'affichait avec 50 lignes vides en haut, car toute grille était complétée en carré. Corrigé hors tranches, à la demande de l'humain (branche `fix/post-traitement-grille-rectangulaire`) : la grille suit celle que l'acquisition a prévue, lue dans `<acquisition>_acquisition-parameters.json` par le port `IScanPlanReader` (adaptateur `acquisition_parameters_scan_plan_reader`), et l'interpolation en garde les proportions ; un scan interrompu garde ses lignes prévues vides, et un scan sans description (dont ceux de l'étalon) garde la grille carrée, aux chiffres identiques. La tranche 2 prolonge ce lecteur pour l'objet et les angles, derrière le même port. Sur ce PC, l'étalon et les 2 tests de 180° échouent déjà sur `develop` sans la correction : l'étalon fait sur le Mac ne s'y reproduit pas à l'identique ; la correction a été vérifiée en comparant, sur ce PC, les sorties avant et après (identiques).
**Décisions de l'humain, 2026-11-16 :** le fichier des paramètres d'acquisition est un contrat entre les deux logiciels, en relation **client-fournisseur** (le post-traitement client, l'acquisition fournisseur) : un besoin du post-traitement peut faire évoluer l'acquisition. Cela remplace, pour ce fichier, le conformisme de la conception (§ 1.1). Les deux écarts relevés par la carte des contextes (`_system/documentation/context-map-acquisition-post-traitement.md`, § 6) se corrigent en tranche 2 : les angles appliqués lus dans l'export au lieu des angles idéaux, et l'empreinte du `.h5` que le traitement rend fausse. Pour l'empreinte, décidé par l'humain : l'acquisition n'exporte plus que des CSV (source brute unique), et le post-traitement crée le `.h5`, où il regroupe les données brutes relues des CSV, ses cinq étapes et leur provenance (CSV source, son SHA-256, `provenance.activity.id`). Premier besoin du client envers l'acquisition : retirer `Hdf5ScanExportPort` du service d'export, déclencher le traitement sur le seul CSV, relever la version mineure du schéma (`data.files` sans `.h5`). À revérifier au codage : les attributs de configuration du `.h5` actuel sont tous dans le fichier des paramètres (détail : carte des contextes, § 6).
**Tranche 2, partie 2 faite le 2026-11-19, sur la branche `dev_post_processor`, pas encore fusionnée** (trace `2026-11-19-tranche-2-partie-2-export-csv-seul-et-h5-du-post-traitement/`) : l'acquisition n'exporte plus que le CSV (`Hdf5ScanExportPort` retiré, `IPostProcessingPort.run(csv_path)`), le post-traitement crée son `.h5` (points bruts relus du CSV dans `raw_scan`, cinq étapes, SHA-256 du CSV, `provenance.activity.id`, empreinte déclarée et leur égalité), le schéma des paramètres passe en 1.7 (`data.files` sans `.h5`). Vérifiée : V1 = 233 réussis et les 2 échecs connus, étalon inchangé, V2 = 0 erreur, V3 = 8 réussis ; suite complète : 2188 réussis et les 17 échecs déjà présents avant (aucun nouveau), `solidai verify` à la racine 630 erreurs contre 631 avant.
**Prochaine action :** confirmer la tranche 2 sur les vraies acquisitions du laboratoire (partie 1 sur `develop`, partie 2 sur `dev_post_processor` : un scan réel exporté, un seul CSV dans le dossier, puis le `.h5` créé par « Traiter » ou en fin de scan, sans modifier le CSV), puis fusionner `dev_post_processor` dans `develop` ; ensuite tranche 3. À trancher par l'humain : le `.h5` ne reprend que les points du `_aefi.csv` ; ceux de la sonde de champ restent dans leur CSV d'accompagnement (constat `constat-attributs-de-configuration-de-l-ancien-h5-et-fichier-des-parametres.md`). À proposer à l'humain, hors des tranches 1 à 6 validées : « Traiter en tâche de fond » (le bouton « Traiter » fige la fenêtre pendant le calcul, comme l'ancien traitement au lancement ; un thread ou un processus avec progression, sans changer les résultats).

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
3. Tranches 1 à 6 de la conception, chacune vérifiée par l'humain. Tranche 1 **faite** (traces `2026-11-16-tranche-1-etapes-*`) ; tranche 2 **faite** (partie 1 sur `develop`, partie 2 sur `dev_post_processor`, à confirmer au laboratoire) ; tranches 3 à 6 à faire.

## Constats à ne pas perdre

- Deux tests de calcul échouent depuis avant ce plan : la calibration de phase (écart de 180° sur deux axes) et la soustraction d'amplitude. Tranche 5.
- Un retraitement par lot remplaçait, dans le `.h5`, les angles de la calibration active par les angles idéaux : corrigé en tranche 2 (partie 1), les angles du fichier des paramètres l'emportent.
