# Objectifs — AEFI Acquisition

## Feature en cours : Hardware Configuration Service

### Contexte

Chaque session d'acquisition AEFI implique deux types de paramètres distincts, actuellement gérés manuellement hors de l'application :

**Paramètres hardware (identité du dispositif — stables)** — `aefi_device_config.json`
- Géométrie des sources : distances pairwise entre les 4 sphères (d_S1_S2, d_S1_S3, d_S1_S4, d_S2_S3, d_S2_S4, d_S3_S4), rayon des sphères
- Électronique d'excitation : version carte (AmpliHT_opa462_v2_ASSOCE), chip DDS (ADS131A04)
- Capteur : version (v2b), dimension, calibration (gain, rotation extrinsèque θx/θy/θz), offset Z
- ADC : chip (AD9106), clk_divider, mapping canaux (Ux_re, Ux_im, Uy_re, Uy_im, Uz_re, Uz_im), facteur de conversion V/ADC_count

**Paramètres d'acquisition (variables entre expériences)** — `acquisition_config.json`
- Excitation DDS : fréquence, gains et phases DDS1–4 (générateur de champ + détection synchrone)
- ADC : oversampling, averaging, gains canaux CH1–4, référence de tension

**Paramètres complémentaires**
- Scan : `scan_config.json` — plage XY, pas, vitesse, pattern (snake/step_scan)
- Banc : `bench_config.json` — dimensions physiques, limites mécaniques, position du référentiel source dans le scan
- Capteurs auxiliaires : `additional_sensors_config.json` — IMU (LSM9DS1), lidar

**Référence des schémas JSON** : `C:\Users\manip\Dropbox\Luis\1 PROJETS\1 - THESE\Simulations Numeriques\AEFI_Forward_Problem\AEFI_4Sphere\AEFI_Hardware_Config\`

---

### Problème à résoudre

Aujourd'hui, aucune association formelle n'existe entre un fichier de scan produit et les paramètres hardware/acquisition utilisés. La traçabilité est manuelle. L'objectif est d'implémenter un **service de configuration hardware** dans l'application qui :

1. **Charge et valide** les configs (device, acquisition, scan, bench, capteurs auxiliaires)
2. **Associe** chaque acquisition à un snapshot immuable de ces paramètres au moment du scan
3. **Persiste** ce snapshot avec les données d'acquisition (dans `.aefi_acquisition/scans/`)
4. **Expose** la config active à l'UI et aux autres services (signal processing, post-processing)

---

### Périmètre technique prévu

- **Domain** : value objects `HardwareConfig` (device + acquisition + scan + bench), port `IHardwareConfigRepository`
- **Application** : use-case `LoadHardwareConfigUseCase`, `SnapshotConfigForAcquisitionUseCase`
- **Infrastructure** : adaptateur JSON (`HardwareConfigJsonRepository`) lisant depuis `.aefi_acquisition/configs/`
- **Interface** : panneau de sélection/visualisation de la config active dans l'UI PySide6

---

### Critères de done

- [ ] Un scan produit un fichier de données qui contient (ou référence) le snapshot config complet
- [ ] La config chargée est validée au démarrage (schéma, valeurs obligatoires)
- [ ] L'UI affiche la config hardware active avant de lancer un scan
- [ ] Tests unitaires sur la validation et le snapshot
