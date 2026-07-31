# Objectifs — AEFI Acquisition

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

### Problème à résoudre

Aucune association formelle n'existe entre un fichier de scan et les paramètres utilisés au moment de l'acquisition. La traçabilité est manuelle. L'objectif est d'implémenter un `AcquisitionConfiguration` Value Object et son service associé qui :

1. **Charge et valide** les 5 templates au démarrage
2. **Gèle un snapshot immuable** de la config active au moment où un scan démarre
3. **Persiste ce snapshot** avec les données d'acquisition dans `.aefi_acquisition/scans/`
4. **Expose la config active** à l'UI et aux autres services

> **Note** : `HardwareConfigurationService` (existant) gère les paramètres avancés hardware (registres DDS, PID) via `IHardwareAdvancedConfigurator`. C'est une préoccupation distincte — ne pas confondre.

---

### Plan de développement

#### Phase 0 — Gitignore (sans risque) ✅ FAIT

Complété `.gitignore` pour couvrir les données runtime non encore ignorées :
- `scans/raw_data/*.csv` et `*.fig`
- `.aefi_acquisition/logs/`

Fichiers déjà commités correspondants désindexés (`git rm --cached`), conservés sur disque.

---

#### Phase 0.5 — Clarifier `TestBench` ← prérequis avant tout travail domain ✅ FAIT

**Audit** : aucun des candidats n'était importé par application/infrastructure/interface, et aucun n'avait de tests. Un 3e doublon fantôme a été trouvé en prime : `domain/model/aggregates/aefi_device.py` n'existait pas sur disque mais était importé par `aefi_physics_engine.py` et `json_device_repository.py` — ces deux fichiers étaient donc déjà cassés et morts.

**Décision utilisateur** : tout supprimer (tentative de refactoring jugée "clumsy", à reprendre proprement si besoin).

**Supprimé** :
- `domain/aggregates/bench.py` (`TestBench`)
- `domain/aggregates/aefi_device.py` (doublon `AefiDevice`)
- `domain/model/aefi_device/` (doublon `AefiDevice` + VOs)
- `domain/model/test_bench/` (`BenchCalibrationData`, `ScanningHead`, `WorkingVolume`)
- `domain/services/aefi_physics_engine.py` (cassé, mort)
- `infrastructure/persistence/json_device_repository.py` (cassé, mort)

Suite de tests `src/` (149 tests) vérifiée verte après suppression.

---

#### Phase 1 — Domain : Value Object `AcquisitionConfiguration` (additif)

**Sous-partie `SourceGeometry` + DGP ✅ FAIT (2026-07-24, corrigé 2026-07-29)** — périmètre réduit à cette seule sous-partie pour l'instant (pas encore `AcquisitionConfiguration` ni les 4 autres sous-VOs).

Implémenté dans `shared_kernel` (pas un module domain dédié `source_geometry/` : ce n'est pas un aggregate — pas de racine, pas d'invariant propre à protéger derrière une identité — juste des VOs/service de calcul réutilisables ; et pas non plus sous `value_objects/acquisition_configuration/` comme esquissé plus bas, pas encore d'aggregate root justifiant ce regroupement) :

```
src/domain/shared_kernel/
├── value_objects/
│   ├── source_geometry/          ← grandeurs BRUTES mesurées (D_12..D_34 extrémité-à-extrémité, phi_1..phi_4),
│   │                                 r_i et d_ij (centre-à-centre) exposés en @property dérivées, pas stockées
│   └── source_frame_geometry/    ← résultat DGP : positions P1-P4 (z=0), centroïde, axes, rotation_matrix, is_orthogonal
└── services/
    └── source_frame_solver/      ← SourceFrameSolver.solve() : DGP coplanaire (NOTE - Source Frame Geometry §3-4)
```

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
- Trio Atomique pour chaque fichier (`_intention.md` + `_tests/`)

**Risque** : faible — code additionnel uniquement, rien d'existant modifié.

---

#### Phase 2 — Application : `AcquisitionConfigService` (nouveau service isolé)

Créer `src/application/services/acquisition_config_service/` :

```
acquisition_config_service/
├── i_api_acquisition_config_service.py   ← load(), validate(), get_active() : AcquisitionConfigDto
├── acquisition_config_service.py
├── dtos/
│   └── acquisition_config_dto.py         ← ce que l'UI consomme
└── ports/
    └── i_acquisition_config_repository.py ← outbound : lit les templates
```

Contraintes :
- Aucun import `infrastructure/`
- `get_active()` retourne un `AcquisitionConfigDto` — pas le VO domain directement

**Risque** : faible — service isolé, aucun service existant touché.

---

#### Phase 3 — Infrastructure : `AcquisitionConfigJsonRepository`

Implémente `IAcquisitionConfigRepository`, lit les 5 `config_templates/*.json`, hydrate `AcquisitionConfiguration`.

Placement : `src/infrastructure/config/acquisition_config_json_repository.py`

**Risque** : nul — périphérie pure.

---

#### Phase 4 — Snapshot dans `StepScan` ← étape délicate

Embarquer le snapshot dans l'aggregate de scan au moment du démarrage.

**Décision en suspens — deux options :**

- **Option A (minimal)** : ajouter `config_snapshot: Optional[AcquisitionConfiguration] = None` dans `StepScan`. Rétrocompatible, `None` si pas de config chargée.
- **Option B (event-sourcing)** : le snapshot est porté par l'event `ScanStarted` — pas de champ dans l'aggregate state, la trace est dans l'event log.

Trancher juste avant cette phase, après avoir lu les tests existants de `StepScan`.

**Risque** : modéré — modification d'un aggregate existant et de ses tests.

---

#### Phase 5 — `ScanExportService` : embed du snapshot dans les fichiers de scan

Modifier l'export pour inclure l'`AcquisitionConfiguration` dans chaque fichier produit.

**Format en suspens** :
- JSON embarqué en attribut du fichier HDF5
- ou fichier `scan_YYYYMMDD_HHMMSS_config.json` à côté du `.h5`

**Risque** : faible domain, modéré infra (format fichier).

---

#### Phase 6 — Interface UI (en dernier)

Panneau de visualisation de la config active avant lancement d'un scan.

---

### Critères de done

- [ ] Un scan produit un fichier qui contient (ou référence) le snapshot `AcquisitionConfiguration` complet
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

- [ ] `physical_bench_limits.py` créé, `scan_zone.py` migré sans régression
- [ ] `LineScanConfig` + `LineScanTrajectoryFactory` + tests (theta=0/45/90/-90, n=1)
- [ ] `ZAxisScanConfig` + `ZAxisTrajectory` + `ZAxisScanTrajectoryFactory` + tests
- [ ] Tous les `_intention.md` rédigés (Trio Atomique)
- [ ] Suite complète `uv run pytest src/` verte
