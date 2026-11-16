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
---

# Plan — Post-traitement conforme à l'acquisition

**État :** tranche 1 (conformité de base) faite et fusionnée dans `develop` le 2026-11-16 (`c25ef87c`, `dev_post_processor` conservée) : couches DDD, fenêtre à panneaux Acquisitions, Carte et Logs, lancement qui ne calcule plus, étalon `golden_master_test` inchangé. Vérifiée : V1 = 132 réussis et les 2 échecs connus (180° sur x et y), V2 = 0 erreur, V3 = 8 réussis. À confirmer sur le PC du laboratoire : l'ouverture sur les vraies acquisitions, sans qu'aucun fichier ne change, et un « Traiter » (l'humain n'a vu la fenêtre que sur une copie de données synthétiques).
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
