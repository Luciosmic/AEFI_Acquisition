---
type: constat::sh-agent-os
genere_par: "[[tache - separer test bench calibration et configuration]]"
doc_type: constat
date: 2026-11-13
---

# Affectation de `test_bench` : 11 éléments au domaine configuration, 40 à la calibration, 7 corrections d'hypothèse

**Verdict : la séparation est faisable sans `shared_kernel` nouveau.** La dépendance va dans un seul sens, calibration vers configuration. Sept éléments sur 51 étaient ambigus (14 %), loin du tiers qui arrête la tâche. Un seul demande du code neuf : la racine `Calibration` mêle les deux, elle se scinde en deux racines.

## Règle d'affectation

Calculée sur les imports réels (script de relevé dans le scratchpad de la session, sortie `graphe-domaine.txt`).

1. La configuration dit **ce qu'est le banc** : composants montés, leurs caractérisations, signature matérielle, limites de course.
2. La calibration dit **ce qui a été mesuré dessus** : capteur, géométrie des sources, transmission mécanique, phase de détection synchrone, solveurs, débit et cadence de l'ADC.
3. Un élément de la configuration n'importe jamais la calibration. La calibration importe la configuration (types de composants, signature matérielle). Rien n'est donc partagé des deux côtés.

## Domaine : `domain/test_bench/`

### Va dans `domain/test_bench_configuration/`

| Élément | Raison |
| --- | --- |
| `physical_bench_limits` | Limites de course du banc. Lu par `step_scan`, la configuration de scan et le pilote Arcus, jamais par la calibration. |
| `entities/hardware_component_selection` | Composant monté. N'importe que le nom et le genre de composant. |
| `entities/hardware_component_characterization_entry` | Caractérisation d'un composant. N'importe que `component_characterization`, nom et genre. |
| `events/hardware_component_events` | `HardwareComponentCharacterized` et `HardwareComponentMounted`, portent les deux entités ci-dessus. |
| `repositories/i_hardware_component_repository` | Dépôt des deux entités. |
| `value_objects/hardware_component_kind` | Genre de composant. Importé par les 3 services d'application de la calibration, côté calibration seulement. |
| `value_objects/hardware_component_name` | Nom unique d'un composant. |
| `value_objects/component_characterization` | Grandeurs essentielles d'un genre. N'importe que le genre. |
| `value_objects/hardware_signature` | Noms des cartes et du capteur montés. Importe `hardware_component_name`. La calibration de phase le référence. |
| Nouvelle racine `bench_configuration` (classe `BenchConfiguration`) | Reçoit de `Calibration` les méthodes de composants (voir plus bas). |

### Va dans `domain/test_bench_calibration/`

| Élément | Raison |
| --- | --- |
| Racine `calibration` (classe `Calibration`) | Garde l'indicateur de compensation et les 4 `record_*` de calibration. |
| entities : `sensor_calibration_entry`, `source_geometry_calibration_entry`, `mechanical_transmission_calibration_entry`, `synchronous_detection_phase_calibration_entry` | Entrées de calibration. |
| events : `sensor_calibration_entry_added`, `source_geometry_calibration_entry_added`, `mechanical_transmission_calibration_entry_added`, `synchronous_detection_phase_calibration_entry_added`, `synchronous_detection_compensation_enabled_changed` | Émis par `Calibration`. |
| repositories : `i_sensor_calibration_repository`, `i_source_geometry_calibration_repository`, `i_mechanical_transmission_calibration_repository`, `i_synchronous_detection_phase_calibration_repository` | Dépôts des entrées ci-dessus. |
| services : `source_frame_solver`, `sensor_mounting_solver`, `acquisition_throughput_analysis`, `adc_output_rate_analysis` | Solveurs et analyses. |
| errors : `source_geometry_inconsistent_error`, `sensor_response_degenerate_error` | Levées par les deux solveurs seulement. |
| value_objects : `caliper_measurement`, `source_frame_geometry`, `sensor_mounting_fit`, `sensor_rotation_angles`, `synchronous_detection_phase_calibration_point`, `acquisition_throughput_characterization`, `adc_output_rate_characterization` | Entrées, sorties et résultats de solveurs. |

### Les 7 ambigus, tranchés par les imports

| Élément | Hypothèse de départ | Décision | Pourquoi |
| --- | --- | --- | --- |
| Racine `Calibration` | une racine | **deux racines** | Elle porte 7 méthodes sur les composants (`mount_hardware_component`, `current_mounting`, `resolve_current_hardware_signature`…). La configuration doit avoir sa racine : un agrégat sans racine est le blocage d'origine. |
| `events/active_sensor_rotation_changed` | configuration (« rotation active ») | calibration | Émis par `sensor_calibration_service`, porte `SensorRotationAngles`, personne côté configuration ne l'importe. |
| `value_objects/geometric_configuration_signature` | configuration (« signature géométrique ») | calibration | Importé par `source_geometry_calibration_entry` seulement. Son intention dit qu'il étiquette les entrées de calibration par la géométrie des sphères. |
| `value_objects/rotation_convention` | configuration | calibration | N'est importé que par `sensor_rotation_angles`. |
| `events/sensor_transformation_angles_updated` | non tranché | calibration | Émis par `transformation_service`, qui appelle `sensor_calibration_service`. |
| `value_objects/hardware_signature` | calibration | configuration | Il est construit des noms de composants montés et importe `hardware_component_name`. Le mettre côté calibration ferait importer la calibration par la configuration. |
| `motion_control_service` et `raw_increment_motion` (application) | configuration (limites de course) | calibration | `motion_control_service` appelle `mechanical_transmission_calibration_service` et refuse un banc non calibré (`uncalibrated_bench_test`). Côté configuration, il ferait importer la calibration. Il lit `physical_bench_limits`, ce qui reste permis (calibration vers configuration). |

## Application : `application/test_bench/` (10 services)

| Service | Destination | Raison |
| --- | --- | --- |
| `hardware_component_service` | `application/test_bench_configuration/` | N'importe que des éléments de la configuration. Appelle les méthodes de composants de `Calibration`, qui passent à `BenchConfiguration`. |
| `sensor_calibration_service` | `application/test_bench_calibration/` | Capteur, solveur, événement de rotation. Importe `hardware_component_service` (calibration vers configuration). |
| `source_geometry_calibration_service` | `application/test_bench_calibration/` | Géométrie des sources. |
| `mechanical_transmission_calibration_service` | `application/test_bench_calibration/` | Transmission mécanique. Importe le dépôt et le genre de composant (calibration vers configuration). |
| `synchronous_detection_service` | `application/test_bench_calibration/` | Phase de détection synchrone. |
| `transformation_service` | `application/test_bench_calibration/` | Appelle `sensor_calibration_service`. |
| `acquisition_throughput_characterization_service` | `application/test_bench_calibration/` | Caractérisation de débit, analyse du domaine de calibration. |
| `adc_output_rate_characterization_service` | `application/test_bench_calibration/` | Caractérisation de cadence ADC, analyse du domaine de calibration. |
| `motion_control_service` | `application/test_bench_calibration/` | Voir le tableau des ambigus. |
| `raw_increment_motion` (ports) | `application/test_bench_calibration/` | Seul `motion_control_service` l'importe. |

## Changements de code qui accompagnent le déplacement

1. **Scinder la racine.** `BenchConfiguration` (`domain/test_bench_configuration/bench_configuration.py`) reçoit de `Calibration` : `record_hardware_component_characterization`, `mount_hardware_component`, `current_mounting`, `mounted_component_name`, `current_characterization`, `is_component_already_recorded`, `resolve_current_hardware_signature`. `Calibration` garde le reste. Corps repris tels quels. Le nom `BenchConfiguration` évite qu'un import dans un test soit pris pour une classe de test (préfixe `Test`).
2. **Appelants des méthodes déplacées** : `main.py`, `hardware_component_service`, `mechanical_transmission_calibration_service` (+ son test), `acquisition_conditions_reader`, `acquisition_snapshot_reader` (+ son test). Seul le receveur change (`Calibration.` vers `BenchConfiguration.`).
3. **Tests.** Les 8 tests de composants de `calibration_test.py` passent dans `bench_configuration_test.py`, assertions inchangées, receveur changé. C'est le seul mouvement de tests hors imports ; il suit la méthode qu'ils testent.
4. **Contexte.** `domain/test_bench/test_bench_intention.md` (contexte cohésif provisoire) est remplacé par les intentions des deux racines.

Limite : l'intention `calibration_intention.md` décrit encore les composants matériels dans sa Responsibility ; elle est réécrite à l'étape de séparation, en renvoyant à la racine de configuration.
