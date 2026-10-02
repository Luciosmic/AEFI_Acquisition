# Objectifs — AEFI Acquisition

## État actuel (2026-07-28)

### Ce qui est opérationnel
- `StepScan` agrégat complet — lifecycle, events, trajectoire, export
- `ElectricFieldProbe` agrégat — identité, axes, mesure calibrée en V/m
- Acquisition continue via `AefiAcquisitionService` (ex-`ContinuousAcquisitionService`) — live view, export scan
- Compensation fréquence (NARDA EP-600) intégrée en infrastructure
- Exécuteur scan déplacé en couche application (refactoring boundary scan-executor)
- 3 modes de vitesse motion (slow / medium / fast) sélectionnables depuis l'UI
- Affichage batterie NARDA EP-600 (%, autonomie estimée) à la connexion + bouton refresh manuel
- Référentiel XY translaté centré + étiquetage quadrants DDS
- Chemin d'export scan par défaut sur le Bureau
- `UIConfigStore` déplacé de `infrastructure/` vers `interface/logic/`
- `ConfigBootstrapper` : seed automatique de `.aefi_acquisition/configs/` depuis `config_templates/` au démarrage (commits 386ecf5, 4e39cf7)
- Event audit log : chaque événement domain persisté en JSONL (`.aefi_acquisition/logs/events/`) via `EventAuditLog` abonné en wildcard sur `InMemoryEventBus` — voir `_system/self/event_store.md`
- 236 tests verts

### Tensions domain identifiées (backlog technique)

Tensions ciblées par Phase D1 (branche `worktree-d1-shared-kernel-cleanup`) — **D1 non mergée dans `develop`** ; toutes encore présentes dans le code actuel :

| Tension | Cible D1 | État dans `develop` |
|---------|----------|---------------------|
| `aefi_voltage_measurement.py` dans `shared_kernel/value_objects/acquisition/` | `ProbeRawReading` dans `electric_field_probe/` | ⏳ renommé `AefiVoltageMeasurement` (commit fc4fc5b), encore dans `shared_kernel` |
| Events motion dans `shared_kernel` | `domain/motion/events/` | ⏳ encore dans `shared_kernel` |
| Events `continuous_acquisition_*` dans `shared_kernel` | `domain/electric_field_probe/events/` | ⏳ encore dans `shared_kernel` |
| Events `system_*` dans `shared_kernel` | `domain/system/events/` | ⏳ encore dans `shared_kernel` |
| `is_fly_scan: bool` dans `SpatialScan` | supprimé | ⏳ encore présent |
| `results: List[Dict]` dans `SpatialScan` | supprimé | ⏳ encore présent |
| `ScanPointResult` couplé à `VoltageMeasurement` | `raw_reading: ProbeRawReading` | ⏳ couplage encore actif |
| VOs `excitation/*` dans `shared_kernel` | `domain/electric_field_excitation/value_objects/` | ⏳ encore dans `shared_kernel` |

---

## Feature en cours : AcquisitionConfiguration — Traçabilité config/scan

### Contexte

Chaque session d'acquisition AEFI implique cinq fichiers de configuration, actuellement gérés manuellement hors de l'application :

| Fichier template | Contenu | Stabilité |
|-----------------|---------|-----------|
| `aefi_device_config.json` | Géométrie sources (distances pairwise, r_sphere), capteur (version, calib gain/rotation), ADC (chip, clk_divider, mapping canaux, facteur V/ADC) | Stable — identité du dispositif |
| `acquisition_config.json` | Excitation DDS (fréquence, gains/phases DDS1–4), ADC (oversampling, averaging, gains CH1–4, référence tension) | Variable entre expériences |
| `scan_config.json` | Plage XY, pas, vitesse, pattern (snake/step_scan) | Variable |
| `bench_config.json` | Dimensions physiques banc, limites mécaniques | Semi-stable |
| `additional_sensors_config.json` | IMU (LSM9DS1), lidar — mapping canaux | Stable |

**Référence des schémas JSON** : `C:\Users\manip\Dropbox\Luis\1 PROJETS\1 - THESE\Simulations Numeriques\AEFI_Forward_Problem\AEFI_4Sphere\AEFI_Hardware_Config\`

**Stratégie de versioning** :
- `config_templates/` — git-tracké, source de vérité versionnée (Reference Data)
- `.aefi_acquisition/configs/` — gitignored, copie runtime remplie par l'app au démarrage
- `.aefi_acquisition/scans/` — gitignored, données transactionnelles produites à l'acquisition

---

### Plan de développement

#### Phase 0 — Gitignore ✅ FAIT

#### Phase 0.5 — Clarifier `TestBench` ✅ FAIT

Supprimé : doublons `TestBench`, `AefiDevice`, modules morts `aefi_physics_engine.py` et `json_device_repository.py`.

#### Phase 1 — Domain : Value Object `AcquisitionConfiguration` (additif)

**Sous-partie `SourceGeometry` + DGP — extraite hors de `src/` (2026-07-29)**, ne fait plus partie de cette Phase 1 (pas encore `AcquisitionConfiguration` ni les 4 autres sous-VOs).

Implémentée et validée dans `shared_kernel` (2026-07-24 → 2026-07-29), puis déplacée vers `external_modules/source_geometry/` le temps d'itérer.

**Réintégrée dans le domain `calibration` (2026-10-01)** — le besoin s'est confirmé : reconstruire les positions depuis les mesures au pied à coulisse, les exporter dans le JSON d'acquisition, et les visualiser en direct dans l'onglet de calibration de la géométrie. Un seul langage : l'entrée est `SourceGeometryCalibrationEntry` (ordre `D_S1_S2, D_S3_S4, D_S1_S3, D_S1_S4, D_S2_S3, D_S2_S4`), le résultat `SourceFrameGeometry` est exprimé dans **le** repère source (centroïde, chaque sphère dans son quadrant `x_neg_y_pos`…) ; le repère de travail du solveur (S1 à l'origine) n'est plus exposé. `external_modules/source_geometry/` est supprimé.

- `domain/calibration/services/source_frame_solver/` — reconstruction DGP coplanaire + carré ajusté (historique des corrections dans son intention).
- `domain/calibration/value_objects/source_frame_geometry/` — résultat.
- `domain/calibration/errors/source_geometry_inconsistent_error.py` — chevauchement / triangle qui ne ferme pas ; l'agrégat refuse d'enregistrer une géométrie non reconstructible.
- `SourceGeometryCalibrationService.preview_source_frame` → `OperationResult` (aperçu live, rien d'enregistré).
- Export : `hardware_configuration.source_frame_reconstruction` dans le JSON d'acquisition.
- Non fait : `PointChargeFieldSimulator` suppose toujours un carré parfait.

**Correction 2026-07-29 — le problème était mal posé :** la 1ère version traitait z4 (hauteur de S4) comme une inconnue libre résolue par $z_4=\sqrt{d_{14}^2-x_4^2-y_4^2}$, censée valider la coplanarité après coup. Avec les mesures réelles du banc, ce discriminant devenait négatif — pas un vrai signe de non-planéité, mais l'artefact d'un problème mal posé : les 4 sphères sont coplanaires **par construction du banc** (contrainte connue a priori, pas une hypothèse à tester), donc S4 a 3 distances mesurées ($d_{14},d_{24},d_{34}$) pour seulement 2 inconnues ($x_4,y_4$) — un système réellement sur-déterminé en 2D, pas un problème 3D. Fix : toutes les positions sont résolues avec z=0 imposé ; S4 est résolu par moindres carrés non linéaires (`scipy.optimize.least_squares`) sur les 3 équations de distance, qui distribue correctement le bruit de mesure au lieu de l'injecter dans une hauteur fictive. Plus de flag `is_coplanar` (toujours vrai par construction), plus de `degeneracy_tolerance` sur S4 (le moindres carrés n'a jamais de discriminant à faire échouer).

**Schéma config aligné sur la note (2026-07-29) :** `aefi_device_config.json` stocke maintenant les grandeurs brutes mesurées au pied à coulisse — `sphere_diameters` (phi_i) et `pairwise_distances_ext` (D_ij, extrémité-à-extrémité) — et non plus des distances centre-à-centre pré-calculées à la main. La conversion ($r_i=\phi_i/2$, $d_{ij}=D_{ij}-r_i-r_j$) est déportée dans `SourceGeometry` (properties). **Rappel :** la note "NOTE - Source Frame Geometry" vit uniquement dans le vault Obsidian de Luis (`0_inbox/`) — ce n'est plus dupliqué dans ce dépôt (`config_templates/NOTE - Source Frame Geometry.md` supprimé), c'est la seule source de vérité.

Reste à faire pour compléter Phase 1 : `acquisition_configuration.py` (VO racine) + les 4 autres sous-VOs (`sensor_calibration`, `acquisition_params`, `scan_params`, `bench_dimensions`) quand le besoin se précise.

---

Créer `src/domain/value_objects/acquisition_configuration/` :

```
acquisition_configuration/
├── acquisition_configuration.py   ← VO racine @dataclass(frozen=True), compose les 5 sous-VOs
├── source_geometry.py             ← distances pairwise, r_sphere, incertitudes GUM
├── sensor_calibration.py          ← gain [V/m]/V, rotation θx/θy/θz, version, serial_number
├── acquisition_params.py          ← fréquence Hz, gains/phases DDS1–4, oversampling, averaging
├── scan_params.py                 ← plage XY, pas, vitesse, pattern
└── bench_dimensions.py            ← hauteur, limites mécaniques XY
```

Contraintes :
- Tous `@dataclass(frozen=True)` — immuabilité garantie
- Aucun import hors `domain/` — pas d'IO, pas d'infra
- Trio Atomique pour chaque fichier

**Risque** : faible — code additionnel uniquement.

#### Phase 2 — Application : `AcquisitionConfigService`

Créer `src/application/services/acquisition_config_service/` :

```
acquisition_config_service/
├── i_api_acquisition_config_service.py
├── acquisition_config_service.py
├── dtos/acquisition_config_dto.py
└── ports/i_acquisition_config_repository.py
```

#### Phase 3 — Infrastructure : `AcquisitionConfigJsonRepository`

Lit les 5 `config_templates/*.json`, hydrate `AcquisitionConfiguration`.  
Placement : `src/infrastructure/config/acquisition_config_json_repository.py`

#### Phase 4 — Snapshot dans `StepScan` ← étape délicate

**Décision en suspens — deux options :**

- **Option A (minimal)** : `config_snapshot: Optional[AcquisitionConfiguration] = None` dans `StepScan`.
- **Option B (event-sourcing)** : le snapshot est porté par `ScanStarted` — pas de champ dans l'aggregate state.

Trancher juste avant cette phase, après avoir lu les tests existants de `StepScan`.

#### Phase 5 — `ScanExportService` : embed du snapshot

Format en suspens : JSON embarqué en attribut HDF5 ou fichier `_config.json` adjacent.

#### Phase 6 — Interface UI

Panneau de visualisation de la config active avant lancement d'un scan.

### Critères de done

- [ ] Un scan produit un fichier contenant le snapshot `AcquisitionConfiguration` complet
- [ ] La config est validée au chargement (champs obligatoires, cohérence des valeurs)
- [ ] L'UI affiche la config active avant de lancer un scan
- [ ] Tests unitaires sur la validation et le snapshot (Fake repository en mémoire)
- [x] `TestBench` et ses doublons clarifiés dans le domain

---

## À trier : analyse scan carré/rectangle centré

`_system/documentation/agent_analysis/06_Scan_Config_Centered_UI_vs_Domain_Analysis.md`
propose des factory methods `ScanZone.centered_square()`/`centered_rect()` (domain)
pour configurer un scan par centre+côté/largeur/hauteur, à coordonner avec
l'extraction `physical_bench_limits.py` prévue ci-dessous. Lire et reprendre ce qui
est pertinent au moment d'implémenter la feature centrée ; sinon archiver la note.

---

## Feature en cours : Scan 1D (ligne theta) & Scan Z

> Branche dédiée `dev_scan` — worktree long-lived pour tous les développements
> scan majeurs à venir (dont le futur flyscan). Cette section trace le plan
> de départ ; voir le plan complet original (avec extraits de code, gabarits
> `_intention.md`, et rapport d'exploration) dans l'historique de conversation
> Claude Code du 2026-07-23/24 si besoin de retrouver le raisonnement détaillé.

### Contexte

Le banc ne fait aujourd'hui que des scans grille 2D (`StepScan`/`StepScanConfig`,
patterns SERPENTINE/RASTER/COMB). Avant de développer le flyscan, on pose une
fondation domaine indépendante :

1. **Scan 1D en ligne** dans le plan XY, orientable par un angle theta.
2. **Scan en Z seul** (x, y fixes).

Le scan Z n'a pas de pilotage moteur automatique aujourd'hui (déplacement
manuel opérateur entre points), mais **le domaine ne doit pas coder cette
distinction** — c'est une préoccupation d'exécution (application/infra) future,
pas une donnée domain.

Cette passe est **strictement domain-only** : aucune modification de
`ScanApplicationService`, `IMotionPort`, `StepScan`/`SpatialScan`, ou
`ScanVisualizationPanel`.

### Décisions actées

- **Formule de rotation** (choisie après clarification utilisateur, une
  formule `y=x·cos(theta)` initialement proposée ne pouvait pas représenter
  un scan pur selon Y) :
  `x(s) = center.x + s·cos(theta)`, `y(s) = center.y + s·sin(theta)`,
  `s` échantillonné symétriquement sur `[-length/2, +length/2]`.
  theta=0°→X pur, 90°→Y pur, 45°→diagonale.
- **`PHYSICAL_Z_MAX_MM = 300.0`** : placeholder explicitement marqué TODO/à
  confirmer hardware, même style que les constantes X/Y existantes (`1200.0`
  hardcodées "pour le MVP" dans `scan_zone.py`).
- **`LineScanConfig`/`ZAxisScanConfig` n'embarquent pas** `stabilization_delay_ms`,
  `averaging_per_position`, `measurement_uncertainty` cette phase — préoccupations
  d'exécution sans lecteur actuel (YAGNI). Ajout additif trivial plus tard.
- **Nouveaux modules restent sous `src/domain/step_scan/`** (pas de nouveau
  bounded context) — seul bounded context "scan spatial" existant, footprint
  trop petit pour un découpage. Dette de nommage notée : le dossier s'appelle
  `step_scan` mais héberge aussi ligne/Z — à trancher si un 3e type de scan
  arrive.
- **Constantes physiques extraites** de `scan_zone.py` vers un module partagé
  `src/domain/shared_kernel/physical_bench_limits.py` (`PHYSICAL_X_MAX_MM`,
  `PHYSICAL_Y_MAX_MM`, `PHYSICAL_Z_MAX_MM`) — 3 consommateurs (ScanZone,
  LineScanConfig, ZAxisScanConfig) = règle des trois atteinte.
- **Ligne à theta=90° ne doit PAS passer par `ScanZone`** : son invariant
  `x_min < x_max` strict rejetterait à tort une ligne verticale (extension X
  nulle). `LineScanConfig` valide sa propre bounding box directement.
- **Convention point unique** (`n_points=1`) : échantillon pris au début de la
  plage (`s=-length/2` pour la ligne, `z_min_mm` pour Z), cohérent avec le
  `step=0` déjà utilisé par `ScanTrajectoryFactory` — pas le centre.

### Fichiers à créer

```
src/domain/shared_kernel/
    physical_bench_limits.py + _intention.md + _tests/

src/domain/step_scan/value_objects/scan_zone/
    scan_zone.py   [MODIFIÉ — import des constantes depuis physical_bench_limits.py,
                     ré-export automatique, scan_zone_test.py ne change pas]

src/domain/step_scan/value_objects/line_scan_config/
    line_scan_config.py + _intention.md + _tests/
    → center: Position2D, length_mm: float, n_points: int, theta_deg: float
    → valide : n_points>=1, length_mm>0, bounding box de la ligne dans les
      limites physiques X/Y (calculée via rotation, pas via ScanZone)

src/domain/step_scan/value_objects/z_axis_scan_config/
    z_axis_scan_config.py + _intention.md + _tests/
    → xy_position: Position2D (fixe), z_min_mm, z_max_mm, n_points
    → valide : xy_position dans limites X/Y, 0<=z_min<z_max<=PHYSICAL_Z_MAX_MM, n_points>=1

src/domain/step_scan/value_objects/z_axis_trajectory/
    z_axis_trajectory.py + _intention.md + _tests/
    → xy_position: Position2D, z_values: List[float] — mêmes ergonomies que
      ScanTrajectory (__iter__/__len__/__getitem__/total_points)

src/domain/step_scan/services/line_scan_trajectory_factory/
    line_scan_trajectory_factory.py + _intention.md + _tests/
    → LineScanTrajectoryFactory.create_trajectory(config) -> ScanTrajectory
      (réutilise ScanTrajectory/Position2D tels quels)

src/domain/step_scan/services/z_axis_scan_trajectory_factory/
    z_axis_scan_trajectory_factory.py + _intention.md + _tests/
    → ZAxisScanTrajectoryFactory.create_trajectory(config) -> ZAxisTrajectory
```

Ne pas toucher : `step_scan.py`, `spatial_scan.py`, `scan_type.py` (mort — 0
usage), `scan_pattern.py`, `scan_axis.py`, `scan_trajectory_factory.py`.

### Vérification

```bash
uv run pytest src/domain/step_scan/value_objects/line_scan_config \
              src/domain/step_scan/value_objects/z_axis_scan_config \
              src/domain/step_scan/value_objects/z_axis_trajectory \
              src/domain/step_scan/services/line_scan_trajectory_factory \
              src/domain/step_scan/services/z_axis_scan_trajectory_factory \
              src/domain/shared_kernel/_tests/physical_bench_limits_test.py -v

uv run pytest src/ -v   # non-régression complète (149+ tests existants, dont scan_zone)
```

### Hors scope (phases futures)

- Intégration dans `StepScan`/`SpatialScan` ou nouvel aggregate ligne/Z.
- Stratégie d'exécution Z (manuelle aujourd'hui, auto plus tard) côté
  application/infra.
- Mode de visualisation 1D dans `ScanVisualizationPanel` (actuellement heatmap
  2D `imshow` uniquement).
- Ajout de `stabilization_delay_ms`/`averaging_per_position`/`measurement_uncertainty`
  aux nouvelles configs.

### Critères de done

- [x] `physical_bench_limits.py` créé, `scan_zone.py` migré sans régression
- [x] `LineScanConfig` + `LineScanTrajectoryFactory` + tests (theta=0/45/90/-90, n=1)
- [x] `ZAxisScanConfig` + `ZAxisTrajectory` + `ZAxisScanTrajectoryFactory` + tests
- [x] Tous les `_intention.md` rédigés (Trio Atomique)
- [x] Suite complète `uv run pytest src/` verte (2026-10-01 : 745 passed ; seul échec = le
      test de timing intermittent `scan_differential_mode_integration_test`, déjà connu, vert en isolé)

Note d'implémentation : `LineScanConfig` tolère 1e-9 mm sur les bornes — `cos(90°)≈6e-17`
rejetait à tort une ligne verticale posée sur le bord x=0.

### Exécution du scan ligne — FAIT (2026-10-01)

Le scan ligne s'exécute de bout en bout depuis l'UI (vérifié headless avec vrais widgets sur
mock stack : 11 points à 45°, diagonale de heatmap remplie). Suite : 763 passed.

- *Domain* : `StepScan` porte la ligne tel quel (même aggregate, même boucle) via
  `LineScanConfig.total_points()` + 4 réglages par point (dupliqués avec `StepScanConfig`,
  marqueur `ponytail:`). `ScanStarted.config: Union[StepScanConfig, LineScanConfig]`.
- *Application* : `execute_line_scan(LineScanConfigDTO)` ; démarrage partagé `_start_scan`.
  Présentation `scan_kind="line"` (extrémités, theta…) ; métadonnées d'export dédiées.
- *Interface* : onglets Grid | Line dans `ScanControlPanel` (persistés dans
  `scan_default_config.json`).
- *Visualisation* : `ScanVisualizationPanel.initialize_line(...)` — mode ligne, chaque vue
  trace valeur vs distance depuis le départ (mm), quel que soit theta. Points placés par
  projection sur la ligne. Remplace l'ancienne projection heatmap creuse (`line_heatmap_grid`,
  supprimé).
- *Panels de visualisation* : une seule classe `ScanVisualizationPanel(profiles=, channels=)`,
  4 instances — « AEFI Voltage Map Plot » / « AEFI Voltage Profiles Plot » (6 canaux tension),
  « Narda Map Plot » / « Narda Profiles Plot » (`channels=()` : composantes de champ créées au
  premier point, selon la sonde). Chaque panel : vue « Single Channel » ou « All Channels ».
  Profils : X ou Y constant, lignes cochables (Tout / Aucun).
  « Narda » = libellé UI provisoire de la sonde de champ électrique ; les ids de panels restent
  `electric_field_*`.

**Reste ouvert :**
- Post-traitement auto en fin de scan (`aefi_post_processor_module`) : non vérifié sur un CSV
  ligne — s'il suppose une grille, il échouera en tâche de fond (le scan et l'export restent OK).
- Nom de fichier d'export toujours `stepScan` (c'est bien l'aggregate `StepScan`).
- Z : hors scope pour l'instant (`ScanPointResult` n'a qu'une `Position2D` → Z perdu).

---

## Roadmap d'évolution domain

L'ordre est imposé par les dépendances : AcquisitionConfiguration d'abord, puis nettoyage domain comme prérequis structurel au multi-capteurs et au fly-scan.

**Prochaine étape architecturale après D1 + AcquisitionConfiguration :** Établir la Context Map (cf. IDDD ch.3). Le refactoring D1 a révélé les sous-domaines réels de l'application (electric_field_probe, motion, excitation, step_scan). Avant D2/D3, formaliser : (1) les frontières du unique Bounded Context "AEFI Acquisition", (2) les relations avec les systèmes externes (post_processor_module ; cube_visualizer réintégré dans src/ le 2026-10-01), (3) le rôle des adaptateurs infrastructure comme ACL implicite face au vocabulaire hardware (steps, pulses → mm, V/m).

---

### Phase D1 — Nettoyage `shared_kernel` ✅ FAIT — EN ATTENTE DE MERGE

**Branche worktree** : `worktree-d1-shared-kernel-cleanup` (commit `2ad1317`)  
**Statut** : terminée sur la branche D1. **Non mergée dans `develop`** — les tensions listées ci-dessus restent ouvertes. Note : `develop` a renommé `VoltageMeasurement` en `AefiVoltageMeasurement` (commit fc4fc5b, 23 juillet) mais l'a conservé dans `shared_kernel` ; la cible D1 reste `ProbeRawReading` dans `electric_field_probe/`.

**Contenu de `shared_kernel` après nettoyage (atteint) :**
- `DomainEvent` base, `IDomainEventBus`
- `OperationResult`, `ValidationResult`
- `Position2D` (primitive géométrique partagée)
- `MeasurementUncertainty`
- `SensorReading` (protocole — introduit en D2)

**Migrations réalisées :**

| Depuis | Vers | Statut |
|--------|------|--------|
| `shared_kernel/events/motion_*` | `domain/motion/events/` | ✅ |
| `shared_kernel/events/position_updated` | `domain/motion/events/` | ✅ |
| `shared_kernel/events/emergency_stop_triggered` | `domain/motion/events/` | ✅ |
| `shared_kernel/events/continuous_acquisition_*` | `domain/electric_field_probe/events/` | ✅ |
| `shared_kernel/events/sensor_transformation_angles_updated` | `domain/electric_field_probe/events/` | ✅ |
| `shared_kernel/events/system_*` | `domain/system/events/` | ✅ |
| `shared_kernel/value_objects/acquisition/VoltageMeasurement` | `domain/electric_field_probe/value_objects/ProbeRawReading` | ✅ |
| `shared_kernel/value_objects/excitation/*` | `domain/electric_field_excitation/value_objects/` | ✅ |
| `shared_kernel/value_objects/hardware_configuration/*` | Application layer | ✅ (`HardwareAdvancedParameterSchema`) |

**Nettoyage structurel dans `step_scan/entities/spatial_scan/`** :
- Supprimer `is_fly_scan: bool` (discriminant de type — inutile avec des agrégats séparés)
- Supprimer `results: List[Dict]` (doublon fantôme des `_points` typés)

**Renommage `VoltageMeasurement` → `ProbeRawReading`** :

`VoltageMeasurement` est trompeur : le NARDA EP600 sort directement en V/m (pas en Volts). Le VO doit représenter "ce qui sort de l'interface capteur", quelle que soit l'unité physique. Le nom `ProbeRawReading` est neutre.

Pour le NARDA : l'adaptateur infrastructure produit un `ProbeRawReading` dont les valeurs sont déjà en V/m. La calibration domain `SensorCalibration(gain=(1,1,1), rotation=identity)` est une identité — zéro cas spécial.

**`ElectricFieldProbe` redesigné (non frozen) :**

```python
@dataclass
class ElectricFieldProbe:
    # Identity — immuable
    brand: str
    model: str
    serial_number: str
    axis_labels: Tuple[str, ...]
    # Calibration — mutable (update_calibration() déclenche un event)
    calibration: SensorCalibration   # gain par axe + matrice rotation/orientation
    # État de connexion
    is_connected: bool = False

    def calibrate(self, raw: ProbeRawReading) -> FieldMeasurement:
        return self.calibration.apply(raw)

    def update_calibration(self, new_calibration: SensorCalibration) -> None: ...
    def connect(self) -> None: ...
    def disconnect(self) -> None: ...
```

`SensorCalibration` VO porte le gain par axe ET l'orientation de la sonde dans le repère (matrice rotation). Quand la sonde est repositionnée physiquement, seule la rotation change — `update_calibration()` est appelé.

**`ScanPointResult` stocke le brut :**

```python
@dataclass(frozen=True)
class ScanPointResult:
    position: Position2D
    raw_reading: ProbeRawReading   # conservé pour recalibration a posteriori
    point_index: int
```

La `FieldMeasurement` (V/m) est dérivée à la demande : `probe.calibrate(point.raw_reading)` ou via le snapshot de calibration dans `AcquisitionConfiguration`.

**Recalibration sans re-acquisition** : `scan.config_snapshot.sensor_calibration.apply(point.raw_reading)`.

**Résultat (branche D1)** : 183 tests verts (177 baseline + 6 nouveaux : `ProbeRawReading`, `SensorCalibration`, `ElectricFieldProbe`). Shims supprimés. Branche en attente de merge dans `develop`. La suite `develop` compte 236 tests (features 23-28 juillet incluses).

---

### Phase D2 — Abstraction multi-capteurs [après D1]

**Objectif** : `ScanPointResult` doit accueillir n'importe quel type de mesure sans modifier l'agrégat scan.

**Contexte** : d'abord d'autres sondes EF (axes différents, calibration différente), mais l'architecture doit être ouverte pour d'autres grandeurs physiques (capteur capacitif, courant, etc.).

**Stratégie : protocole `SensorReading` dans `shared_kernel`**

```python
# shared_kernel/value_objects/sensor_reading.py
from typing import Protocol, Tuple
from datetime import datetime

class SensorReading(Protocol):
    """Minimal contract for any raw sensor reading stored in a scan point.
    
    timestamp est obligatoire — requis pour la corrélation temporelle du fly-scan.
    """
    timestamp: datetime
    def raw_values(self) -> Tuple[float, ...]: ...
```

- `ProbeRawReading` implémente `SensorReading` implicitement (structural typing Python)
- `ScanPointResult.raw_reading: SensorReading` — plus de couplage direct à `ProbeRawReading`
- Pas de changement pour le code existant (duck typing)

**Nouveau capteur — pattern d'intégration** :
1. Créer `domain/<sensor_name>/` avec son agrégat, ses VOs, ses events
2. Son VO de mesure brut implémente `SensorReading` (timestamp + raw_values)
3. Son VO de mesure calibrée (ex : `CapacitanceMeasurement`) est produit par son propre service de calibration
4. Réutilise `ScanPointResult` via le protocole sans modification

**Risque** : faible — structural typing, pas de changement de signature.

---

### Phase D3 — FlyScan [après D2]

> **2026-10-01 — fly-scan simple en cours sur `dev_scan`** (plan et avancement : `_system/ops/tasks.md`,
> « Fly-scan : transmission mécanique au domaine, puis projection en direct »). Une première version (non
> commitée) plaçait les mesures en fin de ligne ; lancée dans l'appli elle a planté — elle est remplacée par une
> projection **en direct à vitesse constante**, la vitesse venant de la calibration (transmission mécanique au
> domaine). Choix de cette passe, à revoir lors du refactoring du domaine prévu ensuite : même agrégat `StepScan`
> et même grille que le step-scan (`StepScanConfig.fly_scan`), pas d'agrégat `FlyScan` ni d'entité `FlyScanLine`.

**Objectif** : scan rapide en mouvement continu — la sonde acquiert en permanence pendant que les moteurs se déplacent.

**Modèle d'acquisition** : sampling continu + corrélation position via profil de vitesse constant

```
FlyScanLine : start_position (x₀,y₀) ──────────────→ end_position (x₁,y₁)
              t_start                                  t_end

Pour chaque ProbeRawReading(timestamp=t) acquis pendant la ligne :
    α = (t - t_start) / (t_end - t_start)
    position = start_position + α × (end_position - start_position)
```

La règle "profil de vitesse constant" est une **règle domain** encodée dans `FlyScanCorrelationService`. Pas de stream de positions moteur à corréler — uniquement les horodatages de début et fin de ligne.

**`FlyScanLine` : entité avec lifecycle en 3 phases**

```
FlyScanLine (entity)
├── id: FlyScanLineId           ← UUID interne (les lignes ne sont pas exportées seules)
├── line_index: int
├── start_position: Position2D
├── end_position: Position2D
├── status: FlyScanLineStatus   ← PENDING → IN_PROGRESS → ACQUIRED → CORRELATED
│
├── t_start: Optional[datetime]                          ← set at IN_PROGRESS
├── t_end: Optional[datetime]                            ← set at ACQUIRED
├── raw_measurements: List[ProbeRawReading]              ← accumulés pendant IN_PROGRESS
└── correlated_results: Optional[List[FlyScanPointResult]] ← set at CORRELATED
```

Phase ACQUIRED : t_end enregistré, liste raw_measurements gelée. Phase CORRELATED : `FlyScanCorrelationService` a été appliqué — seule voie vers CORRELATED.

**Structure `domain/fly_scan/`** :

```
fly_scan/
├── fly_scan.py                         ← agrégat (composition — pas d'héritage SpatialScan)
│                                          id: ScanId (timestamp: scan_YYYYMMDD_HHMMSS)
│                                          status: FlyScanStatus (sans PAUSED)
│                                          lines: List[FlyScanLine]
├── fly_scan_intention.md
├── entities/
│   └── fly_scan_line/fly_scan_line.py  ← entité : lifecycle PENDING→ACQUIRED→CORRELATED
├── value_objects/
│   ├── fly_scan_config/                ← vitesse de scan [mm/s], grille (pas de step/settle)
│   ├── fly_scan_point_result/          ← position interpolée + ProbeRawReading
│   └── fly_scan_status/                ← enum séparé : PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
├── events/
│   ├── fly_scan_started/
│   ├── fly_scan_line_acquired/         ← émis quand t_end enregistré (ACQUIRED)
│   ├── fly_scan_line_correlated/       ← émis quand corrélation terminée (CORRELATED)
│   └── fly_scan_completed/
└── services/
    └── fly_scan_correlation_service/   ← calcul pur, règle vitesse constante
        FlyScanCorrelationService.correlate(line: FlyScanLine) → List[FlyScanPointResult]
```

**`FlyScan` par composition** (pas d'héritage) :

`FlyScan` et `StepScan` ne partagent pas de classe de base dans le code. Ils partagent des *concepts* (ScanId, ScanPointResult, export) mais via la couche application, pas via l'héritage. Avantage : un agent IA lit `FlyScan` de façon autonome sans traverser la hiérarchie.

**Application service `FlyScanService`** :
- `start_fly_scan(config: FlyScanConfig) -> FlyScanId`
- `acquire_line(scan_id, line_index, start_pos, end_pos) -> FlyScanLineId`
- `record_reading(line_id, raw: ProbeRawReading) -> None`
- `close_line(line_id, t_end: datetime) -> None` → déclenche corrélation
- Orchestre : moteur → commandes de ligne, probe → acquisition continue, corrélation ligne par ligne

**Différence fondamentale avec StepScan** :

| StepScan | FlyScan |
|----------|---------|
| Arrêt à chaque point | Mouvement continu |
| Position exacte au moment de la mesure | Position interpolée (vitesse constante) |
| 1 mesure = 1 position | N mesures/ligne → interpolation |
| `ScanPointAcquired` par point | `FlyScanLineCorrelated` par ligne |
| Settle time dominant | Vitesse limitée par sample rate ADC |
| Héritage `SpatialScan` | Composition |

**Contraintes hardware à confirmer** :
- Fréquence d'acquisition ADC en mode continu (ADS131A04 → 8 kSPS max)
- Latence USB vers Arcus DMX pour les horodatages t_start/t_end
  - ponytail: `_run_worker_loop` dans `adapter_motion_port_arcus_performax4EX.py:190` capture déjà `start_time = time.time()` juste avant `_internal_move_to()` — c'est le vrai instant de dispatch hardware (queue déjà vidée), pas l'instant d'enqueue de `move_to()`. Un `MotionStarted`-like event existait autrefois publié depuis `move_to()` (donc à l'enqueue, pas au dispatch) ; il a été supprimé (2026-07) car sans abonné. Pour `t_start` de `FlyScanLine`, republier depuis ce point précis du worker plutôt que depuis `move_to()`.
- Buffer mémoire pour une ligne (à calculer selon vitesse × durée de ligne)

**Mitigation** : implémenter d'abord un "fly-scan simulé" — rejouer un step-scan existant en mode continu pour valider la corrélation avant l'intégration hardware.

---

## Annexe : schéma domain cible (modèle final)

```
domain/
├── shared_kernel/                  ← primitives vraiment partagées
│   ├── DomainEvent, IDomainEventBus
│   ├── OperationResult, ValidationResult
│   ├── Position2D
│   ├── MeasurementUncertainty
│   └── SensorReading (Protocol)    ← timestamp + raw_values() — après D2
│
├── electric_field_probe/           ← capteur champ électrique
│   ├── ElectricFieldProbe (aggregate — mutable)
│   │   ├── brand, model, serial_number, axis_labels    [immuable]
│   │   ├── calibration: SensorCalibration               [mutable]
│   │   ├── is_connected                                 [mutable]
│   │   └── calibrate(ProbeRawReading) → FieldMeasurement
│   ├── value_objects/
│   │   ├── ProbeRawReading         ← renommé depuis VoltageMeasurement
│   │   │   (NARDA : valeurs en V/m → SensorCalibration(gain=1) = identité)
│   │   ├── FieldMeasurement        ← calibré, en V/m
│   │   └── SensorCalibration       ← gain par axe + matrice rotation/orientation
│   └── events/
│       ├── FieldSampleAcquired
│       ├── ElectricFieldProbeConnectionChanged
│       └── continuous_acquisition_*  ← migré depuis shared_kernel
│
├── electric_field_excitation/      ← DDS AD9106, source de champ  ← migré + renommé
│   └── value_objects/
│       ├── ExcitationParameters
│       ├── ExcitationMode
│       └── ExcitationLevel
│
├── motion/                         ← positionnement XY Arcus DMX  ← migré
│   └── events/
│       ├── MotionStarted, MotionCompleted, MotionFailed, MotionStopped
│       ├── PositionUpdated
│       └── EmergencyStopTriggered
│
├── system/                         ← cycle de vie applicatif       ← migré
│   └── events/
│       ├── SystemReady, SystemShuttingDown
│       ├── SystemShutdownComplete, SystemStartupFailed
│
├── step_scan/                      ← scan pas-à-pas (existant, nettoyé)
│   ├── StepScan (aggregate, étend SpatialScan — inchangé)
│   │   id: UUID (inchangé)
│   └── value_objects/
│       └── ScanPointResult(position, raw_reading: ProbeRawReading, index)
│
└── fly_scan/                       ← scan continu (nouveau — Phase D3)
    ├── FlyScan (aggregate — composition)
    │   id: ScanId (scan_YYYYMMDD_HHMMSS)
    │   status: FlyScanStatus (PENDING/RUNNING/COMPLETED/FAILED/CANCELLED)
    ├── entities/fly_scan_line/
    │   FlyScanLine : PENDING → IN_PROGRESS → ACQUIRED → CORRELATED
    ├── value_objects/
    │   ├── FlyScanConfig (vitesse, grille)
    │   └── FlyScanPointResult (position interpolée + ProbeRawReading)
    └── services/
        FlyScanCorrelationService (règle : vitesse constante)
```
