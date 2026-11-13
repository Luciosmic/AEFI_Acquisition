---
type: constat::sh-agent-os
genere_par: "[[tache - separer test bench calibration et configuration]]"
doc_type: constat
date: 2026-11-13
---

# Restants du noyau partagé et de `detection_devices` : deux regroupements et un agrégat à juger

**À discuter.** Le noyau est typé (`operation_result_intention.md`, 10 utilisateurs du domaine), ses 10 événements et 2 objets-valeurs à plat lui sont rattachés, `domain_event` et `i_domain_event_bus` sont des atomes. Il reste ce qui demande un choix de l'humain.

## Niveau de regroupement dans le noyau (laissé en place)

D3 et D4 lisent `shared_kernel/<genre>/<nom>/<nom>.py`. Ces dossiers ajoutent un niveau et leurs notes restent signalées :

| Dossier | Contenu | Notes non typées |
| --- | --- | --- |
| `excitation/events/` | 4 événements, un dossier chacun | 4 |
| `excitation/value_objects/` | 5 valeurs, fichiers sans dossier par valeur | 5 |
| `motion/events/` | 9 événements | 9 (+ `motion_intention.md`) |
| `value_objects/acquisition/` | `aefi_voltage_measurement` | 1 |
| `value_objects/geometric/` | `position_2d` | 1 |
| `value_objects/hardware_configuration/` | `hardware_advanced_parameter_schema` | 1 |

Les trois derniers ont le dossier au nom du thème, pas de la valeur. Choix A : les ranger sous `value_objects/<nom>/<nom>.py` et `events/<nom>/` (un déplacement par dossier, imports suivis), puis les rattacher. Choix B : accepter le niveau de regroupement, ce qu'Evans et Vernon ne demandent pas. Recommandation : A.

## `detection_devices` : un agrégat à deux niveaux, sans racine

`domain/detection_devices/` n'a aucune intention et tient trois sous-domaines (`aefi_device/signal_processing`, `electric_field_probes`, `inertial_probe`) plus `lidar`. Même blocage que `test_bench` avant la séparation. La règle D14 ne peut pas le déclarer dans `utilise_par` : 1 erreur `noyau-partage-utilisateurs-ecart` reste (`aefi_corrected_sample.py` et 9 événements importent le noyau). Créer sa racine exige de décider si ce sont trois agrégats de premier niveau (`aefi_signal_processing`, `electric_field_probe`, `inertial_probe`) ou un seul, ce que la tâche ne tranche pas. Recommandation : trois agrégats, comme pour `test_bench`.

## Ce qui reste hors de la tâche

- Les 43 intentions de `application/test_bench_*/` (`service-applicatif`, DTO, ports, doublures) et les chaînes réel et Fake des 5 dépôts de calibration et du dépôt de composants : lots hexagonaux, déjà prévus.
- Les 6 notes `i_*_repository_intention.md` du domaine de test_bench restent `intention-non-typee` : chaque dépôt est déclaré en enregistrement dans sa racine, la note reste comme pour `operator_registry`.
- 5 `trio-incomplet` dans `test_bench_*` : `errors/` (2 erreurs sans `_tests/`), `sensor_transformation_angles_updated`, `acquisition_throughput_characterization`, `adc_output_rate_characterization`, `sensor_mounting_fit` : aucun test n'existe pour eux.
