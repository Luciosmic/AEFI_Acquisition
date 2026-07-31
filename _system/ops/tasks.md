# Tâches actives

## Mesure différentielle (baseline sans excitation + mesure normale)

**Statut** : implémenté en TDD (2026-07-30) — mute()/unmute(), ScanPointResult/events + baseline, boucle différentielle, export CSV, checkbox UI. Suite complète verte (293 passed).

### Principe

À chaque point de scan, en plus de la mesure normale existante (avec excitation), on
acquiert optionnellement une mesure baseline (excitation coupée juste avant) et on
l'associe à la mesure normale. C'est une **extension** : `measurement` (excité) reste
inchangé, on ajoute un champ optionnel `baseline_measurement` à côté.

Le mute/unmute de l'excitation est **électronique** (gain DDS → 0), pas mécanique — son
délai de stabilisation (`differential_settle_delay_ms`) est court et distinct du
`stabilization_delay_ms` moteur existant. Le mute se fait **une seule fois par point**,
partagé entre le canal AEFI primaire et toutes les sondes auxiliaires actives (ex. Narda
EF probe) — ne pas re-toggler l'excitation par canal.

### Fichiers à toucher

- `domain/step_scan/value_objects/scan_point_result/` : `ScanPointResult` + champ optionnel
  `baseline_measurement: AefiVoltageMeasurement | None`
- `domain/step_scan/events/scan_point_acquired/` : `ScanPointAcquired` + champ optionnel
  `baseline_measurement`
- `domain/step_scan/events/electric_field_scan_point_acquired/electric_field_scan_point_acquired.py` :
  + champ optionnel `baseline_field_measurement: FieldMeasurement | None`
- `application/services/excitation_configuration_service/excitation_configuration_service.py` :
  + `mute()` / `unmute()` (gardent mode/fréquence, togglent juste le niveau à 0 puis
  restaurent le niveau précédent)
- `application/services/scan_application_service/scan_application_service.py` :
  - `AuxiliaryProbeChannel.publish_point_result` : signature étendue pour accepter des
    échantillons baseline optionnels (aujourd'hui `Callable[[Any, int, Any, List], None]`,
    l.114)
  - `make_electric_field_probe_channel._publish` (l.124-134) : calculer aussi
    `baseline_field_measurement` si des échantillons baseline sont fournis
  - `_execute_scan_loop` (l.279-479) : restructurer le bloc par point (aujourd'hui
    l.398-442) — si `config.differential_mode` :
    1. `excitation_service.mute()` → délai `differential_settle_delay_ms`
    2. drain + collecte baseline sur `adc_queue` ET chaque `(channel, channel_queue)` de
       `active_channels` (réutilise `_drain_queue`/`_collect_samples` existants)
    3. `excitation_service.unmute()` → délai `differential_settle_delay_ms`
    4. bloc excité existant (l.398-442), inchangé
    5. attacher les baselines aux résultats avant `ScanPointResult(...)` et
       `channel.publish_point_result(...)`
- `application/services/scan_application_service/dtos/scan_dtos.py` : `Scan2DConfigDTO` +
  `differential_mode: bool = False`, + `differential_settle_delay_ms: float`
- `application/services/scan_export_service/scan_export_service.py` (`_flatten_point`) et
  `infrastructure/persistence/csv_scan_export_port.py` (`write_point` + `write_field_point`) :
  + colonnes `baseline_*` (vides si non différentiel)
- UI : case à cocher "Mesure différentielle" dans le panneau de config scan →
  `Scan2DConfigDTO.differential_mode`

Pas de nouveau VO type `DifferentialMeasurement` — le delta (excité − baseline) se calcule
à la volée à l'export/post-traitement, pas stocké dans le domaine.

### Validation déterministe en mode MOCK (important — priorité de ce chantier)

Le mock stack existant simule déjà le couplage excitation↔acquisition et permet de
prouver le mécanisme de mute de façon déterministe, sans hardware :

- `infrastructure/mocks/adapter_mock_i_acquisition_port.py::RandomNoiseAcquisitionPort` —
  bruit gaussien avec `seed` optionnel pour reproductibilité (mettre `noise_std=0.0` pour
  un test 100% déterministe sans bruit).
- `infrastructure/mocks/adapter_mock_i_excitation_port.py::MockExcitationPort` — stocke
  `last_parameters` à chaque `apply_excitation()`.
- `infrastructure/mocks/adapter_mock_excitation_aware_acquisition.py::ExcitationAwareAcquisitionPort` —
  lit `excitation_port.last_parameters` à chaque `acquire_sample()` et applique un offset
  3D déterministe proportionnel au niveau d'excitation (`avg_level/100.0`), **nul quand le
  niveau est à 0** (`DEFAULT_EXCITATION_OFFSET_MAP`, l.88-94 et check `avg_level > 0`,
  l.163). C'est exactement le point qui prouve que le mute fonctionne : offset=0 pendant
  la fenêtre mutée, offset≠0 pendant la fenêtre normale.
- Wiring de référence : `src/main.py:150-222` — c'est ainsi que ces trois mocks sont déjà
  composés ensemble quand `HARDWARE_CONFIG["acquisition"] == "mock"` et
  `HARDWARE_CONFIG["excitation"] == "mock"`.

Test à écrire (application ou scan_application_service niveau intégration, avec les
fakes) : construire ce même stack (`RandomNoiseAcquisitionPort(noise_std=0.0, seed=...)`
→ `ExcitationAwareAcquisitionPort` → `MockExcitationPort`), lancer un scan en mode
différentiel sur au moins un point, puis vérifier :
1. `baseline_measurement` du point == mesure brute sans offset (puisque `mute()` doit
   avoir mis le niveau à 0 avant l'acquisition baseline)
2. `measurement` (excité) == mesure brute + offset attendu du mode d'excitation configuré
3. la différence `measurement - baseline_measurement` reconstruit exactement le vecteur
   d'offset attendu (avec `noise_std=0.0`, égalité exacte ; sinon tolérance sur la moyenne
   après `averaging_per_position` échantillons)

C'est le test qui valide que le cycle mute→collecte→unmute→collecte fonctionne de bout en
bout dans `ScanApplicationService`, sans dépendre du hardware réel.

### Ordre TDD suggéré

1. `ExcitationConfigurationService.mute()/unmute()` + tests unitaires
2. `ScanPointResult` + `baseline_measurement` (VO/entité, tests domain)
3. `ScanApplicationService` : test d'intégration avec le mock stack ci-dessus (le test qui
   compte le plus — voir section précédente) avant de coder la boucle
4. Implémentation de la boucle différentielle
5. Events (`ScanPointAcquired`, `ElectricFieldScanPointAcquired`) + export CSV
6. UI (case à cocher)
