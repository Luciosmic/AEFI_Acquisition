---
type: service-applicatif::solidai-hexagonal
tldr: "Enchaîner les cinq étapes du traitement d'un scan (grille, calibration de phase, soustraction d'amplitude, rotation de repère, interpolation) et les ranger, sans connaître ni pandas ni h5py."
code: ["[[external_modules/aefi_post_processor_module/application/post_processing_service/post_processing_service.py]]", "[[external_modules/aefi_post_processor_module/application/post_processing_service/no_scan_plan_reader.py]]", "[[external_modules/aefi_post_processor_module/application/post_processing_service/no_acquisition_provenance_reader.py]]"]
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
  - ^: i-acquisition-provenance-reader
    type: port::solidai-hexagonal
    tldr: "read(csv_path) : l'activité et l'empreinte du CSV que l'acquisition a consignées dans son fichier de paramètres, ou rien si aucune description ne les dit."
    sens: sortant
    code: "[[external_modules/aefi_post_processor_module/application/post_processing_service/ports/i_acquisition_provenance_reader.py]]"
  - ^: i-step-writer
    type: port::solidai-hexagonal
    tldr: "save_step, load_step, record_source, save_raw_scan, processing_history, close : créer le fichier d'une acquisition au besoin, y ranger les points bruts relus du CSV, les étapes et la provenance, et les relire."
    sens: sortant
    code: "[[external_modules/aefi_post_processor_module/application/post_processing_service/ports/i_step_writer.py]]"
---
# post_processing_service — Intention

## Rationale

Le traitement d'un scan vivait dans une classe qui lisait le CSV avec pandas, appelait les calculs et écrivait l'HDF5 elle-même. Sans service, le panneau Acquisitions de la fenêtre (tranche 1.7) devrait instancier cette classe et son fichier, et aucun test ne pourrait vérifier l'enchaînement sans disque.

## Responsibility

- `process_scan(ProcessScanDTO)` : lire le scan, construire la grille (celle que l'acquisition a prévue quand sa description la donne, sinon la grille carrée), calibrer la phase, soustraire l'amplitude, tourner le repère si des angles sont donnés (de préférence ceux que l'acquisition a appliqués), interpoler sauf demande contraire, ranger chaque étape.
- Consigner dans le fichier d'étapes sa source : le CSV relu, son SHA-256 (que le lecteur de CSV calcule sur les octets lus), l'identifiant de l'activité et l'empreinte du CSV que l'acquisition a consignées dans son fichier de paramètres, et si les deux empreintes sont égales ; ranger avec elles les points bruts relus du CSV, une fois la grille construite. Un CSV qui n'est plus celui que l'acquisition a haché est traité quand même, avec un avertissement (`pipeline.source_changed`) et `source_sha256_matches` à faux dans le fichier.
- Rendre un `ProcessingSummaryDTO` : étapes faites, erreurs, succès, fichier, historique.
- Journaliser chaque étape dans les mêmes événements que l'ancien pipeline (`pipeline.started`, `pipeline.step`, `pipeline.finished`, `pipeline.failed`), et l'origine de la grille (`pipeline.grid`, en avertissement quand un point tombe hors de la grille prévue).

## Design

- Le lecteur de CSV, l'écrivain d'étapes, le lecteur de la grille prévue et le lecteur de la provenance arrivent par le constructeur (sans lecteur de provenance, `NO_ACQUISITION_PROVENANCE` : la source n'est consignée que par son empreinte) ; sans lecteur de grille prévue, le service prend `NO_SCAN_PLAN` (`no_scan_plan_reader.py`), un lecteur qui ne connaît aucune grille, et chaque scan reçoit la grille carrée ; les calculs sont ceux du domaine, créés à chaque traitement avec les paramètres de la demande.
- Un échec d'étape est journalisé puis relancé, comme avant : l'appelant (l'acquisition) l'attrape.
- Sans angles de rotation, l'étape `rotated_frame` n'est pas écrite, et l'interpolation prend l'étape précédente.
- Les angles de rotation viennent d'abord de la demande `applied_rotation_angles` (ceux que l'acquisition a appliqués, lus dans son fichier de paramètres par le catalogue), à défaut de `parameters.rotation_angles` (les angles idéaux du gabarit). Le service ne lit pas le fichier : il décide seulement de la priorité, et le journal dit la source (`pipeline.rotation_source … source=acquisition_parameters|request|none`). Sans description de l'acquisition, rien ne change, ce que l'étalon `golden_master_test` prouve.
