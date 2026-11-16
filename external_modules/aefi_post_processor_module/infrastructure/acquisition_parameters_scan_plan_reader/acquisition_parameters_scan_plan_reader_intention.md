---
type: adaptateur::solidai-hexagonal
tldr: "Lire la grille prévue d'un scan (zone et nombre de points par axe) dans le fichier des paramètres d'acquisition rangé à côté de son CSV."
code: ["[[external_modules/aefi_post_processor_module/infrastructure/acquisition_parameters_scan_plan_reader/acquisition_parameters_scan_plan_reader.py]]"]
cause_de_changement: outil
implements: ["[[external_modules/aefi_post_processor_module/application/post_processing_service/post_processing_service_intention^^i-scan-plan-reader]]"]
---
# acquisition_parameters_scan_plan_reader — Intention

## Rationale

L'acquisition écrit, à côté de `<acquisition>_aefi.csv`, un fichier `<acquisition>_acquisition-parameters.json` qui décrit le scan prévu (`procedure.step_scan.zone` et `procedure.step_scan.grid`, présents du schéma 1.0 au schéma 1.4, scans pas à pas comme scans à la volée). Sans lecteur de ce fichier, le traitement ne pouvait pas distinguer un scan rectangulaire d'un scan interrompu.

## Responsibility

- Implémenter `IScanPlanReader` : trouver le fichier des paramètres par le nom du CSV, lire la zone et le nombre de points de chaque axe, rendre la grille prévue.
- Ne rien rendre, en le journalisant, pour un CSV que l'acquisition n'a pas nommé, un fichier absent, illisible ou incomplet, ou des bornes dans une autre unité que le millimètre des coordonnées du CSV.

## Design

- Une classe, `json` et `pathlib` ; la même suite de contrat que son Fake.
- Ne lit que la grille prévue. La lecture du reste du fichier (objet mesuré, angles appliqués) est la tranche 2 du plan « post-traitement conforme » : elle prolonge ce lecteur ou le remplace par un lecteur des paramètres complet, derrière le même port.
