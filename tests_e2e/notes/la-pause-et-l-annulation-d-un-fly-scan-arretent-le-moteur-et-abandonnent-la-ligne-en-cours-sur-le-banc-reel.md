---
type: data-note::sk-data
tldr: "Quatre scans du 2026-10-30, faits au banc avec l'infrastructure réelle et non les mocks, ont validé le rollback de ligne du fly-scan : la pause et l'annulation arrêtent le moteur Arcus et n'exportent que les lignes commitées."
about:
  - "[[src/application/scan/scan_application_service/scan_application_service_intention]]"
  - "[[src/application/scan/scan_application_service/ports/i_unit_of_work_intention]]"
  - "[[src/infrastructure/in_memory_unit_of_work/in_memory_unit_of_work_intention]]"
  - "[[src/domain/aefi_line/events/aefi_line_abandoned/aefi_line_abandoned_intention]]"
  - "[[src/infrastructure/hardware/arcus_performax_4ex/adapter_motion_port_arcus_performax4ex/adapter_motion_port_arcus_performax4ex_intention]]"
  - "[[src/application/scan/scan_export_service/scan_export_service_intention]]"
---
# La pause et l'annulation d'un fly-scan arrêtent le moteur et abandonnent la ligne en cours, sur le banc réel

Ces quatre scans sont des tests de l'application, pas des mesures.
Ils ont été faits le 2026-10-30 au banc avec l'infrastructure réelle : contrôleur moteur Arcus Performax 4EX, ADC et générateur réels, aucun mock ni fake.
Leurs journaux ne citent aucun mock, et le premier porte une erreur `LIMIT` renvoyée par le vrai contrôleur Arcus.
L'objet mesuré saisi, `test_rollback`, n'est qu'une étiquette d'essai : aucun objet n'était posé.

Ils servaient la dernière preuve manquante du rollback de ligne : l'arrêt du moteur par `stop()` sur le vrai contrôleur, jusque-là testé sur le fake seulement.

| Dossier | Scan | Ce qu'il teste | Issue |
| --- | --- | --- | --- |
| `2026-10-30_183126_stepScan_step-scan` | pas-à-pas, 3 × 3 points, zone Y 0–30 mm | mise en route | échoué : fin de course Arcus (`LIMIT`) vers y ≈ 0 |
| `2026-10-30_183158_stepScan_step-scan` | pas-à-pas, 3 × 3 points, zone Y 10–40 mm | mise en route, zone corrigée | terminé, 9 points |
| `2026-10-30_183256_flyScan_fly-scan` | fly-scan, 3 lignes | pause en cours de ligne puis reprise | terminé : une ligne abandonnée puis refaite depuis son début, 3 lignes exportées sans doublon |
| `2026-10-30_183355_flyScan_fly-scan` | fly-scan, 3 lignes | annulation en cours de ligne | annulé : export limité à la ligne commitée |

Résultats relevés au banc :

- Pause : moteur immobile moins de 0,41 s après la commande, 13 mm avant la fin de ligne ; la ligne est abandonnée, puis refaite entière après la reprise.
- Annulation : arrêt du moteur en 382 ms ; seules les lignes commitées sont exportées.
- Le cas « échec en cours de ligne » n'a pas été provoqué au banc.

Anomalies vues pendant ces tests, hors rollback :

- La zone Y 0–30 mm a été acceptée alors que le banc touche sa fin de course vers y ≈ 0. Après l'erreur, X a poursuivi son déplacement, et le CSV a enregistré la position commandée (y = 0) au lieu de la position réelle (0,17 mm).
- Un mouvement interrompu par `stop()` publie `MotionCompleted` au lieu d'un événement « arrêté ».
- L'appel `stop()` n'est pas tracé dans le journal de l'adaptateur Arcus.

Les fichiers de chaque dossier (CSV, HDF5, paramètres d'acquisition, événements, journal) restent hors git, à côté de cette note dans `tests_e2e/`.

## Dette

- Le rollback sur échec en cours de ligne n'est pas validé au banc — à lever par : un fly-scan au banc dont un mouvement échoue en cours de ligne
