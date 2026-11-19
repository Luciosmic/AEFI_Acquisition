---
type: service-applicatif::solidai-hexagonal
tldr: "Service applicatif `scan_export_service` : S'abonner aux événements domain du scan (`ScanStarted`, `ScanPointAcquired`, `NardaPointAcquired`, `ScanCompleted`, `ScanFailed`, `ScanCancelled`) et streamer chaque point vers les ports d'export au fil de l'acquisition — pas un transfert."
code: ["[[src/application/scan/scan_export_service/scan_export_service.py]]"]
cause_de_changement: orchestration
---
# scan_export_service — Intention

## Rationale

Isoler la logique d'export des résultats de scan dans un service dédié pour préserver la cohésion de `ScanApplicationService`. L'export (CSV) implique des opérations I/O qui ne doivent pas alourdir le service principal de scan. Le déclenchement du post-processing en aval (module tiers `aefi_post_processor_module`) est aussi porté ici plutôt que par la UI, car il dépend directement du CSV que ce service vient d'écrire.

## Responsibility

- S'abonner aux événements domain du scan (`ScanStarted`, `ScanPointAcquired`, `NardaPointAcquired`, `ScanCompleted`, `ScanFailed`, `ScanCancelled`) et streamer chaque point vers les ports d'export au fil de l'acquisition — pas un transfert différé en fin de scan.
- Exporter chaque scan en CSV seul, dans son dossier d'acquisition : source brute unique, que le post-traitement relit pour créer son propre HDF5 (décision de l'humain du 2026-11-16, appliquée le 2026-11-19 ; l'acquisition n'écrit plus de HDF5, donc l'empreinte des fichiers du document de paramètres ne devient plus fausse).
- Écrire le document de paramètres d'acquisition (`<…>_acquisition-parameters.json`) une fois par acquisition (scan et série temporelle) via `write_metadata`. Objectif : traçabilité complète et reproductibilité — tout ce qui influence une mesure et n'est pas figé dans le code y figure. **Son schéma de référence est `acquisition_parameters/acquisition_parameters_intention.md`** (version cible 1.0 : vues `components` / `measurement_chain`, grandeurs `{value, unit}` UCUM, provenance PROV, objet mesuré, avertissements uniques). Ce JSON porte aussi le sens et l'unité de chaque colonne exportée — pas dans les en-têtes CSV, que `aefi_post_processor_module` lit par nom.
  Depuis le 2026-10-02 (schéma 1.0) : le service ne met plus le document en page. Il rassemble les **faits** — ce que l'acquisition a fait (`ScanActivityDTO` : procédure, excitation réglée, contrôle tenu, sonde, positions du banc, latence USB, issue) et les conditions partagées lues par `IAcquisitionConditionsPort`, `ISoftwareProvenancePort`, `IUsbLatencyTimerPort` — et les remet au port (`write_acquisition_parameters`) au démarrage, puis une seconde fois **après la fermeture de tous les fichiers**, avec l'issue (`completed` / `failed` / `cancelled`) : c'est le port qui liste et hache les fichiers produits. Ports de faits absents → document écrit quand même, faits déclarés inconnus.
- Exporter une lecture continue (`AefiVoltageReadingStarted` → `AefiVoltageSampleAcquired` → `AefiVoltageReadingStopped`) en série temporelle : dossier `<date>_timeSeries_<nom>/`, CSV seul (une ligne par échantillon, `t_s` depuis le premier échantillon), armé explicitement par `configure_time_series_export` puis consommé par la prochaine lecture — les scans démarrent eux aussi le worker ADC continu, ces lectures-là ne doivent pas être exportées.
- Ne tenir aucun event store par acquisition : depuis le 2026-11-19 (schéma 1.6), le service n'est plus abonné à `"*"` et le port n'a plus de `write_event`. Le fichier `<…>_events.jsonl` était trop lourd pour ce qu'on en lisait ; l'audit global de l'application (`.aefi_acquisition/logs/events`) reste. Le port CSV garde `<…>_logs.log` (logs applicatifs teeés pendant la fenêtre du scan), qu'il remplace à l'arrêt par `<…>_logs.log.xz`.
- Exporter la stabilisation de la colonne d'un scan (`ColumnRestMeasured`, `ColumnSettled`) et le flux de l'accéléromètre qui la juge (`InertialProbeSampleAcquired`), par `ColumnStabilizationRecord` : tables `<…>_accelerometer.csv` (dès que l'accéléromètre émet pendant le scan ; remplacée à l'arrêt par `<…>_accelerometer.csv.xz`) et `<…>_column-stabilization.csv` (quand les points sont jugés sur l'accéléromètre), résumé dans `procedure.step_scan.column_stabilization`. Les échantillons arrivent du fil du capteur inertiel : tables ouvertes et écrites sous le verrou des échantillons (`_events_lock`), pour qu'aucune ligne n'atteigne un port en cours de fermeture.
- Déclencher, en fire-and-forget via `IAsyncTaskRunner`, le post-processing (`IPostProcessingPort`) une fois le scan terminé avec succès (`ScanCompleted` uniquement) — le service ne bloque pas et n'attend pas la fin du pipeline.
- Annoncer sur le bus chaque export qu'il ouvre (`AcquisitionExportOpened` : `step_scan`, `fly_scan` ou `time_series`, identifiant, objet mesuré) et sa fermeture, quelle qu'en soit l'issue (`AcquisitionExportClosed`), pour que la garde de fermeture refuse de fermer l'application pendant l'export sans appeler ce service. Les annonces ne passent par aucun port d'export.
- Gérer les erreurs d'export sans affecter le cycle de vie du scan (chaque handler d'événement est protégé par un try/except qui logue plutôt que de propager).

## Design

- **Un seul port d'export** (`csv_export_port`), tenu dans la liste `_active_ports` que les handlers de points parcourent.
- **`IPostProcessingPort` + `IAsyncTaskRunner`** (tous deux optionnels) : le déclenchement est découplé du pipeline de traitement lui-même — ce service ne connaît que « exporté + appelé » sur le chemin du CSV (`run(csv_path)`), jamais « traitement terminé » ni le chemin du HDF5, que le post-traitement crée où son catalogue le cherche.
- **Dépendance directe sur `ExcitationConfigurationService`** (pas un événement) pour lire les paramètres d'excitation courants au démarrage du scan — marqué `ponytail:` en attendant qu'un événement `ExcitationChanged` existe.
- **Injection de dépendances** : tous les ports (`IScanExportPort`, `IAcquisitionConditionsPort`, `ISoftwareProvenancePort`, `IUsbLatencyTimerPort`, `IPostProcessingPort`, `IAsyncTaskRunner`) sont reçus au constructeur.
- Service séparé de `ScanApplicationService` pour respecter le Single Responsibility Principle.
