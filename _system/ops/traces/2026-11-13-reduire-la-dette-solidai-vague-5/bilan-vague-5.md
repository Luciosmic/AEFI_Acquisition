---
type: constat::sh-agent-os
genere_par: "[[tache - reduire la dette solidai vague 5]]"
doc_type: bilan
date: 2026-11-13
---

# Bilan partiel de la vague 5 (arrêt sur demande de l'humain)

**Non terminée, arrêtée à la demande de l'humain.** `solidai verify` passe de 970 à 816 erreurs. Arbre propre, tout est commité. mypy et pytest complets non relancés en fin de vague : les contrôles de chaque lot sont des pytest ciblés verts (dernier gros : 1 045 verts, 3 sautés, application et infrastructure).

## Lots faits

| Lot | Commit | Verify avant → après |
| --- | --- | --- |
| 1a `detection_devices` en 4 dossiers domaine (`aefi_signal_processing`, `electric_field_probes`, `inertial_probe`, `lidar`) et 3 contextes application | `e98f9a2` | 970 → 972 (D14 provisoire) |
| 1b racines typées de `aefi_signal_processing` et `electric_field_probes`, 18 intentions enfants, `utilise_par` du noyau | `e6e0220` | 972 → 952 |
| 2 adaptateurs et Fakes sous `hardware/<appareil>/` : esp32 `330bdb0`, narda `6e9ee2b`, oscilloscope `05814fa`, serial_link `ebb894a`, lsm9ds1 `24080f8`, arcus `0ee5852`, AD9106 et ADS131A04 remontés au niveau `hardware/` `6eb551e`, leurs adaptateurs `1f9630a` `512a542`, micro_controller `e0ce7c6`, `5a42a3a` | voir à gauche | 952 → 923 |
| 3a six doubles de `mocks/` sous le `fake/` de leur réel, avec 5 tests minimaux et une intention | `30b846a` | 923 → 914 |
| 3b `src/main_intention.md`, `point-de-composition` (par le gate) | `7af91be` | 914 → 883 |
| 4 tests de caractérisation de 67 atomes du domaine (événements, objets-valeurs, erreurs, énumérations, identifiants) | `dcbe437`, `3fcee97` | 883 → 816 |

## Constats à discuter

1. **`inertial_probe` et `lidar` n'ont pas de racine** (leur intention dit « pas d'agrégat à ce stade ») : leurs événements et `lidar_distance` restent non typés, et 1 erreur D14 demeure (`inertial_probe` importe le noyau sans pouvoir être nommé dans `utilise_par`). Choix : créer une vraie racine quand la détection de stabilité arrive, ou déplacer les 3 événements dans le noyau.
2. **`main.py` à la racine de `src/`** : son intention typée donne +1 `cause-contredit-la-couche` (un outil hors `infrastructure/` et `interface/`).
3. **Composition matérielle** (`hardware_composition_root`, `composition_root_arcus`, `mcu_composition_root`) : le type exige `cable` vers au moins un adaptateur typé, or aucun adaptateur matériel ne l'est encore.
4. **Doubles de `mocks/` laissés en place** : le composite `adapter_mock_excitation_aware_acquisition` ; `adapter_mock_i_export_port` (aucun import, à supprimer ?) ; `adapter_mock_hardware_config_provider` (import mort vers `domain.value_objects`, second double du même port) ; les deux doubles d'exécuteur (le déplacement ajouterait une erreur H20, aucune suite de contrat n'existe) ; les deux simulateurs physiques.
5. **`composite_hardware_initialization_port`** : le ranger dans son dossier ne gagne rien (aucun test, +1 `trio-incomplet`).
6. **Tests non générés** : erreurs à constructeur validé (`aefi_line`, `scan`), `scan_started` (valeurs d'exemple refusées par `ScanZone`), noyau et `spatial_scan`.

## Reprise

Prochaine étape exacte : lot 5, `intention-non-typee` de l'application (`service-applicatif` et enregistrements `port`, d'abord `application/test_bench_calibration` 40 et `application/shared` 20), puis les adaptateurs matériels et de persistance (`adaptateur`, `implements`), puis `cable` de `hardware_composition_root`, `composition_root_arcus`, `mcu_composition_root`. Ensuite : mocks d'exécuteur (constat 4), pytest complet et mypy complets avant bilan final.
