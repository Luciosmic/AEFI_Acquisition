---
doc_type: constat
---

# Le golden master voit une dérive, mais pas celle que le découpage citait

Étape 1.1. L'étalon est `_tests/golden/` (3 scans × 5 étapes = 15 comparaisons de tableaux, plus les métadonnées) et `_tests/golden_master_test.py`.
Scans : `scan_001_baseline`, `scan_004_rotation_z45` (angles du manifeste) et `scan_008_incomplete_nan` (les 1800 premières lignes de `scan_001_baseline`, soit 36 rangées sur 50 : 4200 NaN par étape, 68400 sur la grille interpolée).

## Constat : `border_width` est sans effet

Le découpage demande de changer `border_width` de 1 à 2 dans `ProcessingPipeline` et d'attendre un échec.
Le test passe : `PrimaryFieldPhaseCalibrator` et `PrimaryFieldAmplitudeSubtractor` stockent `border_width` sans jamais le lire (docstring « Deprecated, kept for backward compatibility »).
Log : `pytest-golden-master-avec-border-width-2.log` (3 réussis).

## Preuve de sensibilité retenue

Changement temporaire de `interpolation_method` de `'cubic'` à `'linear'` dans `ProcessingPipeline` : les trois tests échouent sur l'étape `interpolated` (`pytest-golden-master-avec-interpolation-linear.log`), puis le changement est annulé par `git checkout` et le test repasse (3 réussis).

Décision : cette preuve remplace celle du découpage, dont le paramètre est mort. Le découpage doit être corrigé (le paramètre `border_width` n'est pas une dérive observable).

## Autres décisions

- `.npz` est ignoré par le `.gitignore` de la racine : `_tests/golden/.gitignore` (`!*.npz`) le rend versionnable, sans toucher à la racine.
- Le test relit les étapes dans le `.h5` avec h5py, sans `DataHandler`, pour survivre à son remplacement en 1.4. Le seul champ exclu est `timestamp`.
- Les étapes sont comparées en égalité exacte : une plateforme différente (PC de labo sous Windows) peut produire un écart de dernier bit sur l'interpolation ; à surveiller si le test y est un jour lancé.
