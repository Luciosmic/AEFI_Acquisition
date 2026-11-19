---
type: constat::sh-agent-os
genere_par: "[[tache - reduire la dette solidai vague 5 suite]]"
doc_type: bilan
date: 2026-11-13
---

# Bilan de la vague 5, suite

**Atteint, avec une réserve.** `solidai verify` passe de **816 à 616 erreurs** (avertissements de co-changement 142 → 182, attendu). mypy **2 941** (référence 2 943). pytest **1 849 verts, 3 sautés** (référence 1 709 : +140 tests de caractérisation de la vague 5, 0 échec). `au_diagnostics` : seulement les 2 erreurs yaml anciennes.

La réserve : les 3 composition roots, les adaptateurs, les services et les DTO sont typés, mais 51 intentions de ports restent comptées « non typées » par A20 (constat 2), et trois familles attendent l'humain.

## Contrôles de départ

pytest 1 849 verts. mypy donnait 3 086 : 143 `no-untyped-def` dans les tests de caractérisation de la vague 5, corrigés par `-> None` (`5ea9fe87`). Corrigés ensuite : 66 `# type: ignore` sur les lignes de ces tests qui violent exprès un type (`ed6d0a2d`), que l'annotation faisait enfin vérifier.

Le lot 1a de la vague précédente (`e98f9a2`) avait commité par erreur deux dossiers non suivis venus de Dropbox (`src/domain/electric_field_probe/`, `src/domain/step_scan/events/electric_field_scan_point_acquired/`), dont deux tests cassent la collecte pytest. Retirés de l'index, restés sur disque (`5fca97cf`).

## Lots

| Lot | Commits | Verify avant → après |
| --- | --- | --- |
| 1 `main.py` déplacé dans `interface/` (A15), références suivies : `launch.sh/.bat/.ps1`, `main_mock.py`, `CLAUDE.md` ; lancement mock vérifié 25 s en headless | `a59db2ec` `58733dbf` `3947a267` | 816 → 815 |
| 2 racines `inertial_probe` et `lidar` | sauté, constat 1 | — |
| 5a `application/shared` : 19 intentions typées | `e43bc351` | 815 → 798 |
| 5b `test_bench_calibration` et `test_bench_configuration` : 43 | `478e19f8` | 798 → 760 |
| 5c scan, frequency_sweep, inertial_probe, registres, signal, sonde : 30 | `f9ef68d5` | 760 → 730 |
| 5d liste `ports:` en liens refusée par le moteur (33 erreurs), retirée | `d7cfc64f` | 730 → 730 |
| 6a infrastructure : 82 intentions (adaptateurs avec `implements`, Fakes avec `double_de`, autres en atome outil) | `42f1f233` | 730 → 634 |
| 6b trois composition roots en `point-de-composition`, `cable` 2, 4 et 9 adaptateurs | `ef2a2bb3` | (avec 6a) |
| 7 13 événements du noyau partagé rangés sous `shared_kernel/events/` et typés (D4) ; 49 fichiers de références suivis | `2b2fe7fb` | 634 → 621 |
| 8 Rationale ajouté à 5 docstrings de ports `i_api` (H5) | `cf8d35c5` | 621 → 616 |

Les intentions de `application/` et `infrastructure/` ont été écrites par script natif, pas une par une par le gate (92 + 82 appels) ; `au_diagnostics` est resté propre.

## Erreurs restantes (616)

110 `test-applicatif-importe-un-reel`, 120 `intention-non-typee` (51 ports et interfaces de repository, 34 interface, 17 infrastructure, 15 domaine…), 74 `dto-non-gele`, 64 `service-depend-hors-de-ses-ports`, 44 `methode-publique-hors-api`, 35 `trio-incomplet` (outils, pas des atomes de domaine), 28 `infrastructure-importe-hors-des-ports`, 22 `service-instancie-ses-dependances`, 21 `adaptateur-mal-place`, 19 `fake-mal-place`, 14 `service-incomplet`, 11 `service-appelle-un-service`, 10 `adaptateur-construit-hors-composition`, le reste sous 8 chacune. Les familles de code (DTO, services, imports) touchent des signatures publiques : hors du périmètre « sans changer le comportement » de cette vague.

## Ce qui reste à l'humain

1. `intentions-de-ports-hors-de-a20-a-discuter.md` : accepter `port` dans A20, ou suivre H5 jusqu'au bout (51 fichiers).
2. `adaptateurs-de-persistance-et-d-execution-a-discuter.md` : un dossier par adaptateur, ou par thème (21 + 19 erreurs).
3. `racines-inertial-probe-et-lidar-a-discuter.md` : racine minimale, ou événements dans le noyau.
4. Hérités de la vague 5 : doubles de `mocks/` laissés (le déplacement ne gagne rien sans suite de contrat H20), deux simulateurs physiques, interfaces de repository du domaine sans enregistrement inline (bloquent 4 adaptateurs `in_memory_*`), widgets et presenters d'interface non typés (`presenter` demande un port entrant `i_api` typé).
5. Le générateur de tests de caractérisation de la vague 5 (script de session, hors repo) n'écrivait ni `-> None` ni les marques `type: ignore` : à corriger s'il resert.
