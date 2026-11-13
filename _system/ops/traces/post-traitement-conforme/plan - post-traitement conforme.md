# Plan — Post-traitement conforme à l'acquisition

**État :** journal du post-traitement fait (2026-11-12) ; conception de l'architecture en panneaux et récits utilisateurs écrits, à valider.
**Prochaine action :** faire valider par l'humain `2026-11-12-concevoir-l-architecture-par-panneaux/conception - post-traitement en panneaux.md` (et ses trois points à trancher), puis coder la tranche 1, la conformité de base.

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
3. Tranches 1 à 6 de la conception, une par commit, chacune vérifiée par l'humain.

## Constats à ne pas perdre

- Deux tests de calcul échouent depuis avant ce plan : la calibration de phase (écart de 180° sur deux axes) et la soustraction d'amplitude. Tranche 5.
- Un retraitement par lot remplace, dans le `.h5`, les angles de la calibration active par les angles idéaux. Tranche 2.
