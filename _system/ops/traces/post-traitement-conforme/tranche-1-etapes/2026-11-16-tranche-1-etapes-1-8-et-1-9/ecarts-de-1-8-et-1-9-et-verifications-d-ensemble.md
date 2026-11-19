---
doc_type: constat
type: constat::sh-agent-os
genere_par: "[[tache - tranche 1 etapes 1 8 et 1 9]]"
---

# Étapes 1.8 et 1.9 : écarts au découpage, vérifications d'ensemble, à confirmer au laboratoire

Écritures faites avec les outils natifs (le gate `au` n'a pas été utilisé). Typage `constat::sh-agent-os` non fait : à la charge de la session.

## Écarts au découpage

1. **Le journal gagne la ligne `acquisition.state scan=… state=… detail=…`**, écrite à chaque affichage de la liste (un test du presenter la garde). Le découpage demandait « le journal contient l'état à recalculer » sans dire sous quelle forme. L'état est écrit avec le libellé du panneau (« à recalculer », « traitée », « en échec »).
2. **`--repo-path` ne saute plus rien** : il désigne seulement le dossier d'export. `--force` traite tout au lancement, avec ou sans `--repo-path`. L'adaptateur de `src/` lance `--repo-path <dossier>` sans `--force` : son comportement est celui d'avant (il avait déjà calculé lui-même).
3. **Le lanceur `launch/launch_post_processor.bat`** lance `composition_root.py` sans argument : il ouvre désormais la liste sans calculer. Rien à changer (hors périmètre, `launch/` intact).
4. **`diagrams/sequence_diagrams.puml` n'est pas du post-traitement** (analyse du bruit : `AnalysisPipeline`, `NoiseAnalyzer`…) : laissé tel quel ; la séquence du traitement est en mermaid dans `Data Processing Architecture.md`. `class_diagrams.puml` est réécrit ; `test_concept_diagram.puml` et `test_design_diagram.puml` décrivent la stratégie de test analytique, encore vraie.
5. **`.venv` du dépôt principal** : lien symbolique vers `~/.venvs/AEFI_Acquisition` daté du 2026-11-12, ignoré par git, avant ce travail : laissé en place (aucun `.venv/` n'est apparu dans le worktree).

## Vérifications d'ensemble (1.9)

| Commande | Worktree | Après fusion, dépôt principal sur `develop` |
|---|---|---|
| V1 | 132 réussis, 2 échecs connus | 132 réussis, 2 échecs connus (180° sur x et y) |
| V2 | 0 erreur, 46 vérifications | 0 erreur, 46 vérifications |
| V3 | 8 réussis | 8 réussis |
| `solidai verify --entry . --target .` | 631 erreurs, 180 avertissements | non relancé : `develop` avant fusion = 632 erreurs, 180 avertissements |

Comparaison de la racine : les deux listes ne diffèrent que d'une ligne, en moins côté worktree (l'intention du journal sans type, typée en 1.2). Aucune erreur nouvelle. Les 631 erreurs restantes sont de l'acquisition (`src/`), hors du plan.
Logs : `solidai-verify-racine-worktree.log`, `solidai-verify-racine-develop.log`, `pytest-v1-1-9-worktree.log`, `pytest-v1-apres-fusion-develop.log` et leurs voisins.

## À confirmer sur le PC du laboratoire

Le critère de 1.9 « l'humain lance `composition_root.py` sur ses vraies acquisitions, voit la liste sans qu'aucun fichier ne change, et traite une acquisition par le bouton » n'est pas vérifiable sur ce Mac : les vraies acquisitions sont sur le PC du laboratoire. L'humain a vu la fenêtre sur une copie de données synthétiques (« oui c'est bien »). Le test de lancement en sous-processus prouve l'absence d'écriture à l'ouverture sur une acquisition synthétique ; le comportement sur de vraies acquisitions (dont les `.h5` créés par l'acquisition sans étapes, qui passent « à recalculer » : règle `incomplete`) reste à voir au laboratoire.

## Limites déjà connues, à décider

- « Traiter » fige la fenêtre pendant le calcul : proposé comme tranche à part, « Traiter en tâche de fond » (plan).
- Le bouton « tout ce qui est à recalculer » ne reprend pas les acquisitions en échec de la session (constat de 1.6 et 1.7).
- Un traitement qui échoue après avoir rangé `preprocessed` laisse des étapes partielles que la règle `incomplete` ne voit pas (constat du catalogue).
