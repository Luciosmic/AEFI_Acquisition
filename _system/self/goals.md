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
