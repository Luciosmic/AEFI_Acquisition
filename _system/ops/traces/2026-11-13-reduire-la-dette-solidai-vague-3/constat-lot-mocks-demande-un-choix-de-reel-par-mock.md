---
type: constat::sh-agent-os
genere_par: "[[tache - reduire la dette solidai vague 3]]"
doc_type: constat
date: 2026-11-13
---

# Le lot des doubles de `infrastructure/mocks/` demande un choix de réel par mock

**Lot sauté, rien n'est déplacé.** Le tri le classe mécanique, mais le geste qu'il propose ne tient pas, et le vrai geste demande un jugement par mock.

## Pourquoi le geste du tri ne tient pas

Pour les 11 fichiers `adapter_mock_*.py`, le tri attend `src/infrastructure/mocks/fake/fake_mocks.py`.
H18 veut `infrastructure/<A>/fake/fake_<A>.py`, **un seul Fake par fichier et par dossier** (`fake_<A>`, `A` étant le dossier de l'adaptateur ou, sous `hardware/`, de l'appareil ou de son adaptateur).
Onze doubles ne tiennent pas dans un seul `fake_mocks.py`.

## Ce que demande la décision de l'humain (« un dossier par appareil »)

Chaque double doit aller sous le `fake/` du réel qui implémente son port.
Le choix du réel n'est pas déductible du nom, et plusieurs doubles visent le même appareil, ce que H18 refuse (un `fake_<A>.py` par dossier) sauf à les répartir par adaptateur.

| Double | Port | Imports hors du dossier | Piste de réel | Point à trancher |
| --- | --- | --- | --- | --- |
| `adapter_mock_i_motion_port` | `IMotionPort` | 18 | `hardware/arcus_performax_4ex/` | le dossier a déjà 2 Fakes mal placés (lots de jugement 3 et 4) |
| `adapter_mock_i_acquisition_port` | `IAcquisitionPort` | 19 | `hardware/micro_controller/ads131a04/` | 2 classes dans le fichier (`MockAcquisitionPort`, `RandomNoiseAcquisitionPort`) : un Fake par fichier |
| `adapter_mock_i_excitation_port` | `IExcitationPort` | 11 | `hardware/micro_controller/ad9106/` | |
| `adapter_mock_excitation_aware_acquisition` | `IAcquisitionPort` + `IExcitationPort` | 3 | aucune | double composite, pas de réel unique |
| `adapter_mock_i_synchronous_detection_hardware_port` | `ISynchronousDetectionHardwarePort` | 2 | `hardware/micro_controller/ad9106/` | même dossier que l'excitation : un seul `fake_ad9106.py` |
| `adapter_mock_i_hardware_initialization_port` | `IHardwareInitializationPort` | 1 | `hardware/micro_controller/` | |
| `adapter_mock_i_hardware_advanced_configurator`, `adapter_mock_hardware_config_provider` | `IHardwareAdvancedConfigurator` | 0 | `hardware/micro_controller/` | deux doubles du même port, aucun importé hors du dossier |
| `adapter_mock_i_aefi_acquisition_executor` | exécuteur d'acquisition | 21 | à chercher | |
| `adapter_mock_i_inertial_probe_acquisition_executor` | exécuteur sonde inertielle | 2 | `hardware/lsm9ds1/` ? | |
| `adapter_mock_i_export_port` | `IExportPort` | 0 | `persistence/` ? | aucun import hors du dossier : candidat à la suppression |

Le lot entier change des imports dans environ 80 fichiers de test et de composition (colonne « imports », cumul) (`hardware_composition_root.py` construit déjà l'un d'eux en mode simulation).

## Simulateurs physiques, laissés en place

Ils restent des simulateurs (H18) et ne comptent pas dans le lot :
- `src/infrastructure/mocks/cube_sensor_field_simulator.py` (7 imports hors du dossier avec le suivant)
- `src/infrastructure/mocks/point_charge_field_simulator.py`

## Ce qui reste à l'humain

1. Valider ou corriger la colonne « piste de réel » ci-dessus, et dire quoi faire du double composite et des doubles sans import.
2. Une fois le lot 3 de jugement (réels et Fakes sous `hardware/<appareil>/`) fait, déplacer les doubles dans l'ordre : réel d'abord, double ensuite.
