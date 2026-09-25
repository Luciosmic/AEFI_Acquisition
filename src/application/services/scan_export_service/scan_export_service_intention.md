# scan_export_service — Intention

## Rationale

Isoler la logique d'export des résultats de scan dans un service dédié pour préserver la cohésion de `ScanApplicationService`. L'export (CSV + HDF5) implique des opérations I/O qui ne doivent pas alourdir le service principal de scan. Le déclenchement du post-processing en aval (module tiers `aefi_post_processor_module`) est aussi porté ici plutôt que par la UI, car il dépend directement des fichiers que ce service vient d'écrire.

## Responsibility

- S'abonner aux événements domain du scan (`ScanStarted`, `ScanPointAcquired`, `ElectricFieldScanPointAcquired`, `ScanCompleted`, `ScanFailed`, `ScanCancelled`) et streamer chaque point vers les ports d'export au fil de l'acquisition — pas un transfert différé en fin de scan.
- Exporter chaque scan simultanément en CSV et en HDF5 (plus un choix de format interchangeable) dans un même dossier d'acquisition.
- Écrire un snapshot JSON des paramètres d'acquisition (scan, excitation, sonde de champ électrique, config moteur) une fois par scan via `write_metadata`. Ce JSON porte aussi les unités de chaque colonne exportée (`export.units`) — pas dans les en-têtes CSV, que `aefi_post_processor_module` lit par nom.
- Exporter une lecture continue (`AefiVoltageReadingStarted` → `AefiVoltageSampleAcquired` → `AefiVoltageReadingStopped`) en série temporelle : dossier `<date>_timeSeries_<nom>/`, CSV seul (une ligne par échantillon, `t_s` depuis le premier échantillon), armé explicitement par `configure_time_series_export` puis consommé par la prochaine lecture — les scans démarrent eux aussi le worker ADC continu, ces lectures-là ne doivent pas être exportées.
- Tenir un event store par acquisition : abonné à `"*"`, le service transmet via `write_event` tout événement publié pendant qu'un export est ouvert (pas seulement ceux portant le `scan_id` — mouvement, excitation, sonde font partie du contexte à rejouer). Le port CSV l'écrit dans `<…>_events.jsonl`, à côté de `<…>_logs.log` (logs applicatifs teeés pendant la même fenêtre).
- Déclencher, en fire-and-forget via `IAsyncTaskRunner`, le post-processing (`IPostProcessingPort`) une fois le scan terminé avec succès (`ScanCompleted` uniquement) — le service ne bloque pas et n'attend pas la fin du pipeline.
- Gérer les erreurs d'export sans affecter le cycle de vie du scan (chaque handler d'événement est protégé par un try/except qui logue plutôt que de propager).

## Design

- **Deux ports d'export toujours actifs** (`csv_export_port`, `hdf5_export_port`), pilotés en boucle (`_active_ports`) plutôt qu'un port unique sélectionné par format.
- **Timestamp partagé** entre les deux ports au moment de `configure()`, pour garantir qu'ils écrivent dans le même dossier d'acquisition — nécessaire pour que le post-processing retrouve le CSV et le HDF5 ensemble.
- **`IPostProcessingPort` + `IAsyncTaskRunner`** (tous deux optionnels) : le déclenchement est découplé du pipeline de traitement lui-même — ce service ne connaît que « exporté + appelé », jamais « traitement terminé ».
- **Dépendance directe sur `ExcitationConfigurationService`** (pas un événement) pour lire les paramètres d'excitation courants au démarrage du scan — marqué `ponytail:` en attendant qu'un événement `ExcitationChanged` existe.
- **Injection de dépendances** : tous les ports (`IScanExportPort` ×2, `IAcquisitionSnapshotPort`, `IPostProcessingPort`, `IAsyncTaskRunner`) sont reçus au constructeur.
- Service séparé de `ScanApplicationService` pour respecter le Single Responsibility Principle.
