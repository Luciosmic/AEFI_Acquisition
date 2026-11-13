---
type: constat::sh-agent-os
genere_par: "[[tache - separer test bench calibration et configuration]]"
doc_type: bilan
date: 2026-11-13
---

# Bilan : `test_bench` séparé en calibration et configuration, noyau partagé typé

**Atteint.** `solidai verify` passe de 1 031 à 972 erreurs, mypy reste à 2 943, pytest à 1 709 réussis (3 sautés, 0 échec). `domain/test_bench/` et `application/test_bench/` n'existent plus. Aucune erreur `au_diagnostics` nouvelle (les 2 erreurs yaml anciennes : `_system/promise_model`, `_system/thoughts_interface`).

## Les étapes

| Étape | Commits | Verify | Contrôle |
| --- | --- | --- | --- |
| 1 Rangement : `i_acquisition_port` et `aefi_acquisition_service` dans `application/shared/`, `application/services/` supprimé | `c1947ff`, `3038aea` | 1 031 | pytest `shared` et `scan` : 189 verts |
| 2 Affectation | constat `constat-affectation-de-test-bench-a-calibration-ou-configuration.md` | 7 ambigus sur une cinquantaine | pas d'arrêt |
| 3 Séparation : domaine configuration (avec la racine `BenchConfiguration` scindée de `Calibration`), domaine calibration, application configuration, application calibration | `ba929f8`, `ef0d7bc`, `8a6feb8`, `fb9b96b` | 1 031 → 1 021 | pytest ciblé 505 et 692 verts, collecte `src` sans nouvelle erreur |
| 4a Domaine `test_bench_*` : 8 événements et `physical_bench_limits`, 13 objets-valeurs, 6 entités, 2 erreurs, 4 services, 5 dépôts en enregistrements | `bdab0b5`, `15bfaaf`, `4c1db7b`, `1eec694`, `33b316e` | 1 021 → 987 | pytest domaine 153 verts par lot |
| 4b Noyau : typé `noyau-partage` (10 utilisateurs), 10 événements, 2 objets-valeurs rattachés, 2 atomes | `70daab7`, `b65645f`, `d1af3a1` | 987 → 972 | pytest domaine 432 verts |
| 5 Contrôle final | pytest complet, mypy complet, verify, `au_diagnostics` | 972 | voir plus bas |

Le typage du noyau a d'abord été essayé et retiré (`f57f411`, 987 → 1 070) ; D14 a ensuite été restreinte au domaine sur décision de l'humain, voir `constat-typer-le-noyau-partage-fait-monter-verify-de-83-erreurs.md`.

## Ce qui a changé dans le code, hors déplacements

1. **La racine `Calibration` est scindée.** `BenchConfiguration` (`domain/test_bench_configuration/bench_configuration.py`) reçoit ses 7 méthodes de composants et de signature matérielle, corps repris sans changement de règle ; le préfixe des messages de journal passe de « Calibration » à « BenchConfiguration ».
2. **10 tests passent de `calibration_test.py` à `bench_configuration_test.py`**, assertions inchangées. Seul le receveur change, et le nom du journal vérifié par `assertLogs` suit le module. L'assistant `make_hardware_signature` est dupliqué et annoté.
3. **Appelants** : `main.py`, `hardware_component_service`, `mechanical_transmission_calibration_service` et son test, `acquisition_conditions_reader`, `acquisition_snapshot_reader` et son test. Seul le receveur change.
4. **Imports** suivis dans `src`, tests, composition, documents et modèles ; `archives/` et `.claude/worktrees/` ne sont pas touchés.

## Mesures

| | Référence | Final |
| --- | --- | --- |
| `solidai verify` | 1 031 erreurs, 118 avertissements | 972, 143 (co-changement : les imports suivis sur plusieurs couches le font monter, déjà constaté en vague 3) |
| mypy (903 fichiers suivis, cache neuf) | 2 943 | 2 943 |
| pytest `src` (sans les 2 dossiers non suivis) | 1 709 verts, 3 sautés | 1 709 verts, 3 sautés |

## Erreurs restantes dans les familles touchées

| Famille | Erreurs |
| --- | --- |
| `application/test_bench_*` | 43 `intention-non-typee`, 31 `dto-non-gele`, 26 `service-depend-hors-de-ses-ports`, 16 `test-applicatif-importe-un-reel`, 16 `methode-publique-hors-api`, 13 `port-sortant-sans-fake`, 10 `service-instancie-ses-dependances`, 5 `mock-dans-un-test-applicatif`, 5 `service-appelle-un-service`, autres moins de 3 |
| `domain/test_bench_*` | 5 `port-sortant-sans-fake`, 5 `trio-incomplet`, 0 `intention-non-typee` en dehors des 6 notes de dépôts |
| `domain/shared_kernel` | 22 `intention-non-typee` et 26 `trio-incomplet` (les dossiers `excitation/`, `motion/`, 3 dossiers thématiques), 1 `intention-mal-nommee` |
| D14 | 1 : `detection_devices` n'a pas d'intention |

## Ce qui reste à l'humain

1. `detection_devices` : trois agrégats de premier niveau ou un seul ? Débloque le dernier D14 et le typage de ses 3 sous-domaines.
2. `shared_kernel/excitation/`, `motion/` et les 3 dossiers thématiques de `value_objects/` : ranger à plat (A, recommandé) ou accepter un niveau de regroupement (B).
3. `motion_control_service` est rangé côté calibration parce qu'il appelle `mechanical_transmission_calibration_service` : à confirmer, voir le constat d'affectation.
4. Les lots hexagonaux d'`application/test_bench_*` (43 intentions) peuvent maintenant partir.

## Constats produits

- `constat-affectation-de-test-bench-a-calibration-ou-configuration.md`
- `constat-typer-le-noyau-partage-fait-monter-verify-de-83-erreurs.md`
- `constat-restants-du-noyau-partage-et-de-detection-devices.md`
