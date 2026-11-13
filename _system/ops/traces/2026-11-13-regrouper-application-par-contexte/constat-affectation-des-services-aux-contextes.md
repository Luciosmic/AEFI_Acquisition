---
type: constat::sh-agent-os
genere_par: "[[tache - regrouper application par contexte]]"
doc_type: constat
date: 2026-11-13
---

# Affectation des services de `application/services/` aux contextes

**Verdict : 2 dossiers ambigus sur 25 (8 %), sous le seuil d'un quart. Le déplacement peut commencer.**

Méthode : `solidai graphe --format json` sur ACQ (523 nœuds, 1 380 arcs, `run-graphe-json.log`), puis pour chaque service les imports du domaine (dossier de premier niveau, ou deux niveaux sous `test_bench/` et `detection_devices/`) et les appelants (autres services, infrastructure, interface).
Les noms de contexte sont ceux du domaine : `test_bench`, `detection_devices`, `scan` (agrégats `scan`, `step_scan`, `aefi_line`, `narda_point`), `frequency_sweep`, `measured_object_registry`, `operator_registry`.
Le domaine nomme déjà `test_bench`, `scan` et `detection_devices` des « contextes cohésifs » (`src/domain/test_bench/test_bench_intention.md`).
`shared_kernel` du domaine n'est pas un contexte : un service qui n'importe que lui n'a pas de contexte propre.

## Tableau

| Service | Contexte | Raison (imports qui décident) |
| --- | --- | --- |
| `acquisition_throughput_characterization_service` | `test_bench` | domaine : `test_bench/calibration` (2) + noyau ; l'intention de `test_bench` y range le débit ADC |
| `adc_output_rate_characterization_service` | `test_bench` | domaine : `test_bench/calibration` (2) + noyau |
| `hardware_component_service` | `test_bench` | domaine : `test_bench/calibration` (5), rien d'autre |
| `mechanical_transmission_calibration_service` | `test_bench` | domaine : `test_bench/calibration` (4) |
| `sensor_calibration_service` | `test_bench` | domaine : `test_bench/calibration` (8) ; appelle `hardware_component_service` et `source_geometry_calibration_service` |
| `source_geometry_calibration_service` | `test_bench` | domaine : `test_bench/calibration` (6) |
| `synchronous_detection_service` | `test_bench` | domaine : `test_bench/calibration` (4) |
| `transformation_service` | `test_bench` | domaine : `test_bench/calibration` (2) ; appelle `sensor_calibration_service` ; l'appelle `aefi_signal_processing_service` (`detection_devices`), sens permis par l'intention de `test_bench` |
| `motion_control_service` | `test_bench` | domaine : `test_bench/physical_bench_limits` (1) + `shared_kernel/motion` ; appelle `mechanical_transmission_calibration_service` ; seul appelant applicatif : `scan_application_service` |
| `raw_increment_motion` (ports seuls) | `test_bench` | consommé par `motion_control_service` et l'infrastructure matérielle |
| `aefi_signal_processing_service` | `detection_devices` | domaine : `detection_devices/aefi_device` (8) |
| `electric_field_probe_service` | `detection_devices` | domaine : `detection_devices/electric_field_probes` (5) |
| `inertial_probe_service` | `detection_devices` | domaine : `detection_devices/inertial_probe` + `lidar` |
| `lidar_distance` (DTO et ports seuls) | `detection_devices` | domaine : `detection_devices/lidar` (1) ; appelants : l'infrastructure matérielle |
| `scan_application_service` | `scan` | domaine : `step_scan`, `scan`, `aefi_line` (plus de 30 imports) |
| `scan_export_service` | `scan` | domaine : `step_scan` (6), `narda_point` (1) contre `detection_devices/electric_field_probes` (2) ; couplage faible à `detection_devices`, voir ci-dessous |
| `frequency_sweep_service` | `frequency_sweep` | domaine : `frequency_sweep` (5) |
| `measured_object_service` | `measured_object_registry` | domaine : `measured_object_registry` (4) |
| `operator_service` | `operator_registry` | domaine : `operator_registry` (5) |
| `excitation_configuration_service` | `shared` | domaine : `shared_kernel/excitation` seul ; appelé par `scan_application_service`, `scan_export_service`, `frequency_sweep_service` et 3 services de `test_bench` |
| `hardware_configuration_service` | `shared` | domaine : `shared_kernel` seul ; appelé par 2 services de `test_bench`, la configuration avancée et l'infrastructure matérielle (7) |
| `event_log_maintenance_service` | `shared` | domaine : `shared_kernel` seul ; appelants : le journal d'événements de l'infrastructure et son presenter |
| `system_lifecycle_service` | `shared` | domaine : événements du noyau seuls ; appelants : l'infrastructure matérielle et l'interface de démarrage |

## Ambigus (restent dans `application/services/`)

1. `aefi_acquisition_service` : n'importe que le noyau du domaine, donc sans contexte propre, mais il importe `scan_application_service.ports.i_acquisition_port` (contexte `scan`) et il est appelé par `scan`, `test_bench` (3 services) et `frequency_sweep`. Le ranger dans `shared/` ferait dépendre le noyau partagé d'un contexte ; le ranger dans `scan` ferait importer `scan` par `test_bench` et `frequency_sweep`. Une sortie possible : remonter le port `i_acquisition_port` dans `shared/` (action de l'humain, hors de cette vague).
2. `continuous_acquisition_service` : dossier sans module ; il tient deux fichiers de résultat de test (`.json`, `.puml`) écrits par les tests de `aefi_acquisition_service` et de `electric_field_probe_service` (deux contextes), et deux sous-dossiers vides. Il suit `aefi_acquisition_service`.

## Dossiers vides, non suivis par git

`lidar_distance lidar_stream_error/`, `motion_control_service motion_conversion_unavailable_error/`, `raw_increment_motion raw_increment_motion_error/` (noms à espace, chacun ne tient qu'un dossier `errors/` vide) : résidus de renommages, rangés hors du suivi. Ils sont retirés (`rmdir`) à la fin, sans effet sur git.

## Points à discuter (non tranchés ici)

- `scan_export_service` est placé dans `scan`, mais il importe deux modules de `detection_devices/electric_field_probes`. Si l'export de la sonde Narda devient un contexte propre, il se scinde.
- `motion_control_service` et `raw_increment_motion` vont dans `test_bench` parce que leur seul import de contexte est `physical_bench_limits`. Le mouvement des axes pourrait être un contexte propre (le noyau du domaine tient déjà `shared_kernel/motion`) ; la mesure de la fin de tâche donnera son couplage.
- `measured_object_registry` et `operator_registry` forment deux contextes d'un service chacun, comme dans le domaine ; un contexte « registres » les réunirait.
