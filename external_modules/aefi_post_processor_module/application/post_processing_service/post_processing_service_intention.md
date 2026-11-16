---
type: service-applicatif::solidai-hexagonal
tldr: "Enchaîner les cinq étapes du traitement d'un scan (grille, calibration de phase, soustraction d'amplitude, rotation de repère, interpolation) et les ranger, sans connaître ni pandas ni h5py."
code: ["[[external_modules/aefi_post_processor_module/application/post_processing_service/post_processing_service.py]]"]
cause_de_changement: orchestration
ports:
  - ^: i-api-post-processing-service
    type: port::solidai-hexagonal
    tldr: "process_scan(ProcessScanDTO) : traiter un scan et ranger ses cinq étapes."
    sens: entrant
    code: "[[external_modules/aefi_post_processor_module/application/post_processing_service/i_api_post_processing_service.py]]"
  - ^: i-csv-scan-reader
    type: port::solidai-hexagonal
    tldr: "read(csv_path) : les points d'un fichier de scan en tableaux numpy, FileNotFoundError si le fichier est absent."
    sens: sortant
    code: "[[external_modules/aefi_post_processor_module/application/post_processing_service/ports/i_csv_scan_reader.py]]"
  - ^: i-scan-plan-reader
    type: port::solidai-hexagonal
    tldr: "planned_grid(csv_path) : la grille que l'acquisition a prévue pour ce scan, ou rien si aucune description ne la dit."
    sens: sortant
    code: "[[external_modules/aefi_post_processor_module/application/post_processing_service/ports/i_scan_plan_reader.py]]"
  - ^: i-step-writer
    type: port::solidai-hexagonal
    tldr: "save_step, load_step, record_source, processing_history, close : ranger les étapes d'une acquisition et les relire."
    sens: sortant
    code: "[[external_modules/aefi_post_processor_module/application/post_processing_service/ports/i_step_writer.py]]"
---
# post_processing_service — Intention

## Rationale

Le traitement d'un scan vivait dans une classe qui lisait le CSV avec pandas, appelait les calculs et écrivait l'HDF5 elle-même. Sans service, le panneau Acquisitions de la fenêtre (tranche 1.7) devrait instancier cette classe et son fichier, et aucun test ne pourrait vérifier l'enchaînement sans disque.

## Responsibility

- `process_scan(ProcessScanDTO)` : lire le scan, construire la grille (celle que l'acquisition a prévue quand sa description la donne, sinon la grille carrée), calibrer la phase, soustraire l'amplitude, tourner le repère si des angles sont donnés, interpoler sauf demande contraire, ranger chaque étape.
- Rendre un `ProcessingSummaryDTO` : étapes faites, erreurs, succès, fichier, historique.
- Journaliser chaque étape dans les mêmes événements que l'ancien pipeline (`pipeline.started`, `pipeline.step`, `pipeline.finished`, `pipeline.failed`), et l'origine de la grille (`pipeline.grid`, en avertissement quand un point tombe hors de la grille prévue).

## Design

- Le lecteur de CSV, l'écrivain d'étapes et le lecteur de la grille prévue arrivent par le constructeur ; sans lecteur de grille prévue, chaque scan reçoit la grille carrée ; les calculs sont ceux du domaine, créés à chaque traitement avec les paramètres de la demande.
- Un échec d'étape est journalisé puis relancé, comme avant : l'appelant (l'acquisition) l'attrape.
- Sans angles de rotation, l'étape `rotated_frame` n'est pas écrite, et l'interpolation prend l'étape précédente.
