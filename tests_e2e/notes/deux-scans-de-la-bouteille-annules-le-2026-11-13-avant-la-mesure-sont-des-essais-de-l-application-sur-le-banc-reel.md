---
type: data-note::sk-data
tldr: "Deux scans pas-à-pas de la bouteille d'eau, lancés le 2026-11-13 au banc avec l'infrastructure réelle et non les mocks, puis annulés après 5 et 6 points, sont des essais de l'application et non des mesures."
about:
  - "[[src/application/scan/scan_export_service/scan_export_service_intention]]"
  - "[[src/application/scan/scan_export_service/acquisition_name/acquisition_name_intention]]"
  - "[[src/infrastructure/persistence/csv_scan_export_port_intention]]"
  - "[[src/infrastructure/persistence/hdf5_scan_export_port_intention]]"
---
# Deux scans de la bouteille annulés le 2026-11-13 avant la mesure sont des essais de l'application, sur le banc réel

Ces deux scans sont des essais de l'application, pas des mesures.
Ils ont été faits le 2026-11-13 au banc avec l'infrastructure réelle (moteurs Arcus, ADC, générateur), aucun mock ni fake : leurs journaux ne citent aucun mock.
L'objet saisi est la bouteille cristalline de 50 cl d'eau déionisée du registre des objets mesurés.

| Dossier | Scan | Issue |
| --- | --- | --- |
| `2026-11-13_202125_stepScan_` | pas-à-pas, 3 × 3 points | annulé après 5 points |
| `2026-11-13_202628_stepScan_` | pas-à-pas, 150 × 100 points | annulé après 6 points |

Leur nom de dossier finit par `_` sans objet ni lift-off : ils ont été lancés avec la version d'avant 20 h 31, où le nom venait encore du champ libre « base », laissé vide.
Ce défaut a conduit à mettre à jour le banc avec la version qui compose le nom à partir de l'objet et du lift-off.
La mesure réelle de la bouteille a suivi à 20 h 40, avec le même objet et la même zone : `2026-11-13_204052_stepScan_bouteille_cristalline_50cl_eau_deionise_liftoff-25mm`, resté dans le dossier d'export.

Les fichiers de chaque dossier restent hors git, à côté de cette note dans `tests_e2e/`.

## Dette

- Le but exact de ces deux essais (nom de fichier d'export, réglage de la zone ou faux départ) est déduit de leur horaire et de leur nom, pas noté au banc — à lever par : l'opérateur du 2026-11-13
