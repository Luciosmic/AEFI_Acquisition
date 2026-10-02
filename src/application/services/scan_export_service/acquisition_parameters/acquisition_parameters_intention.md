# acquisition_parameters — Intention

> Référence du schéma `acquisition-parameters.json` (version 1.0), écrit à côté de
> chaque export (scan pas-à-pas, série temporelle). Ce fichier est le contrat :
> les scripts d'analyse le lisent, les tests garde-fous l'appliquent.

## Rationale

Sans un document de paramètres complet et organisé, une mesure exportée n'est ni
traçable ni reproductible. Deux exports de septembre 2026 l'ont montré : le débit
et le bruit dépendent de `n_avg` (moyennage MCU) et de l'OSR de l'ADC, et aucun des
deux n'était exporté — impossible de savoir, après coup, avec quel réglage une
série avait été acquise. Pire : l'objet mesuré (« bouteille d'eau à 8 mm des
sphères ») n'existait que dans le nom du dossier.

L'ancien format (`0.2-agile`) avait trois défauts de structure, chacun source
d'erreur silencieuse :

- **Plusieurs logiques de rangement mélangées** (par fichier source :
  `motion_last_config` ; par concept : `excitation` ; par nature :
  `hardware_configuration` / `hardware_settings`). Un même composant était éclaté
  sous deux noms, l'excitation décrite deux fois sans lien entre les deux.
- **« Le plus récent » au lieu de « l'appliqué »** : `sensor_calibration_latest`
  était la dernière entrée du registre, tous montages confondus, alors que la
  rotation réellement appliquée pouvait être un essai, les angles idéaux, ou une
  calibration d'un autre montage.
- **Des noms de fichiers internes dans le format**.

Un composant peut servir plusieurs fonctions (l'AD9106 : DDS1/DDS2 pour
l'excitation, DDS3/DDS4 pour la référence de la détection synchrone, fréquence
commune ; le MCU lit l'ADC et pilote l'AD9106). Une organisation par chaîne de
mesure seule obligerait à le découper ; une organisation par composant seule
perdrait le sens physique. D'où deux vues qui ne se recouvrent pas.

Le vocabulaire et les règles s'alignent sur des standards existants plutôt que
d'en inventer (voir « Standards de référence ») : un lecteur extérieur, un dépôt
de données ou un futur contexte JSON-LD retrouvent des notions connues.

## Responsibility

- Décrire **tout ce qui influence une mesure**, tel qu'appliqué pendant
  l'acquisition, et **ce qui a été mesuré** (objet, grandeurs observées).
- Ranger chaque information **à un seul endroit**, chaque grandeur avec son unité.
- Signaler explicitement, dans une liste unique, tout ce qui est inconnu,
  incomplet ou non reproductible — jamais une omission silencieuse.

## Design

### Principe de complétude

> Tout ce qui influence une mesure et n'est **pas figé dans le code** est exporté.
> Ce qui est figé dans le code (mapping voies ADC → axes I/Q, conversion
> codes → volts, conventions) est couvert par `provenance.software.commit`.

Corollaire : un arbre de travail modifié (`dirty`) rend le code non reproductible
→ avertissement.

### Principe d'unicité (« store each fact once »)

Chaque fait a **une** place. Une information qui se déduit d'une autre est soit
omise, soit déclarée **dérivée** avec sa source (`derived_from`) — jamais une
copie muette. Les identifiants d'entités (calibrations, montage, composants)
vivent là où l'entité est décrite ; pas de liste « used » qui les répéterait.

### Deux vues

- **`components`** — le matériel physique (SOSA `System`). Chaque composant
  apparaît **une seule fois, en entier**. Clés = types de composant du catalogue
  (`HardwareComponentKind` : `signal_generation_chip`, `adc`, `microcontroller`,
  `sensor`, `conditioning_electronics_board`, `excitation_electronics_board`,
  `motors`), plus `electric_field_probe`. Jamais un nom de puce ni de fichier
  comme clé.
- **`measurement_chain`** — les fonctions, dans l'ordre du signal (SOSA
  `Procedure` / `Actuation` / `Observation`). Chaque fonction **renvoie** aux
  composants qu'elle utilise (`uses` : lien portant ses métadonnées — voies, rôle)
  et ne porte que ce qui lui est propre. Elle ne recopie **aucun** réglage.

### Grandeurs : valeur et unité ensemble

Toute grandeur numérique est un objet **quantité** — l'unité voyage avec la
valeur (QUDT `QuantityValue`, SensorThings `unitOfMeasurement`, NeXus `@units`) :

```jsonc
{ "value": 4096, "unit": "1" }                         // sans dimension
{ "value": 127, "unit": "{sample}" }                   // compte
{ "value": 100000.0, "unit": "Hz" }
{ "code": 14673, "value": 80.6, "unit": "deg" }        // code registre + valeur physique
{ "code": 1100, "unit": "{DDS_gain_code}" }            // code registre, conversion inconnue
```

- `unit` : code **UCUM** (lisible par une machine), jamais vide. Grandeur sans
  dimension → `"1"` ; compte ou code → annotation UCUM entre accolades.
- Code registre : `code` (brut, pour rejouer exactement) + `value`/`unit`
  physiques quand la conversion est connue.
- Booléens, énumérations et textes restent des valeurs simples, sans unité.
- Source unique des unités : la spécification des paramètres des configurateurs
  (Hardware Advanced Config, champ `unit`) — l'interface et l'export disent la
  même chose.

### Dates

ISO 8601 **avec décalage horaire**, partout (document et fichiers de données) :
`2026-10-02T14:03:11.123+02:00`. Plus de dates locales sans fuseau à côté de
dates UTC.

### Identifiants

Tout objet décrit porte un identifiant stable (`id`) : acquisition, entrée du
catalogue, montage, entrées de calibration. C'est ce qui permettra de relier des
exports entre eux (toutes les acquisitions faites avec telle calibration).

### Anatomie d'un composant

```jsonc
"<kind>": {
  "component":        { "name": "ADS131A04", "id": "<catalog entry id>", "recorded_at": "…" },
  "characterization": { "full_scale": { "value": 2.442, "unit": "V" },
                        "noise": null },                 // null = non caractérisé → avertissement
  "settings":         { "oversampling_ratio": { "value": 4096, "unit": "1" },
                        "reference_source": "Internal", … }
}
```

- `component` / `characterization` : catalogue des composants (registre domaine,
  composant **monté**). Absent → `component: null` + avertissement.
- Une grandeur caractérisée peut porter `conditions` (fréquence, température…)
  quand le catalogue les enregistre (SSN `SystemCapability` sous
  `OperatingConditions`) — pas encore le cas, voir Questions ouvertes.
- `settings` : ce qui a été **écrit sur le matériel**. Source : état mémoire du
  contrôleur quand il existe (l'AD9106 compensé par la détection synchrone n'est
  pas persisté sur disque), sinon config résolue `default + last` (même fonction
  `resolve_config` que le démarrage). Pas de relecture des registres (chantier
  séparé).
- Un composant sans réglage logiciel (cartes, capteur) n'a pas de `settings`.

### Squelette 1.0

```jsonc
{
  "schema": { "name": "aefi-acquisition-parameters", "version": "1.0" },

  "provenance": {                                   // PROV-O : activité, agents
    "activity": { "id": "…", "kind": "step_scan | time_series",
                  "started_at": "…", "ended_at": "… | null",
                  "status": "running | completed | failed | cancelled",
                  "failure_reason": null },
    "software": { "name": "AEFI Acquisition", "commit": "…", "branch": "…", "dirty": false },
    "operator": { "name": "… | null" },
    "generated_at": "…"
  },

  "feature_of_interest": {                          // SOSA : ce qui est mesuré
    "description": "bouteille d'eau, 8 mm du contact avec les sphères, résistance 350 kΩ",
    "notes": null
  },

  "procedure": {                                    // SOSA Procedure : ce qui a été demandé
    "step_scan": {
      "zone": { "x_min": { "value": …, "unit": "mm" }, … },
      "grid": { "x_nb_points": …, "y_nb_points": …, "total_points": … },
      "pattern": "SNAKE", "fast_axis": "Y",
      "stabilization_delay": { "value": …, "unit": "ms" },
      "averaging_per_position": { "value": 20, "unit": "{sample}" },
      "measurement_uncertainty": { "value": …, "unit": "V" },
      "differential": { "enabled": false, "settle_delay": { "value": 50.0, "unit": "ms" } },
      "estimated_duration": { "value": …, "unit": "s" }
    },
    "time_series": { "max_duration": null }
  },

  "components": {
    "signal_generation_chip":         { "component": {…}, "characterization": {…},
                                        "settings": { "frequency": {…Hz…},
                                                      "channels": { "1".."4": { "digital_gain": {…code…}, "phase": {…code + deg…}, "offset": {…} } },
                                                      "link_dds1_dds2": true, "enforce_dds3_dds4_quadrature": true, … } },
    "adc":                            { …, "settings": { "oversampling_ratio", "clkin_divider", "iclk_divider",
                                                         "reference_voltage", "reference_source", "high_resolution",
                                                         "negative_charge_pump", "channels": { "1".."8": { "gain", "enabled" } } } },
    "microcontroller":                { …, "settings": { "n_avg": { "value": 127, "unit": "{sample}" } } },
    "motors":                         { …, "settings": { "step_size": { "value": 21.8, "unit": "um/{step}" }, …,
                                                         "speed_mode": "fast", "referential": "centered" } },
    "sensor":                         { "component": {…}, "characterization": {…} },
    "conditioning_electronics_board": { … },
    "excitation_electronics_board":   { … },
    "electric_field_probe":           { "component": { "brand", "model", "serial_number" },
                                        "settings": {…connexion…}, "state": { "battery": { "value": …, "unit": "%" } } }
  },

  "measurement_chain": {
    "excitation": {                                 // SOSA Actuation
      "uses":  [ { "component": "signal_generation_chip", "channels": ["1", "2"] },
                 { "component": "excitation_electronics_board" } ],
      "state": { "mode": "X_DIR",
                 "level_s1_s2": { "value": 20.0, "unit": "%" }, "level_s3_s4": { "value": 20.0, "unit": "%" },
                 "derived_from": "components.signal_generation_chip.settings" },
      "sources": { "geometry_calibration": { "id": "…", … }, "reconstruction": { … } }
    },
    "sensor": {
      "uses": [ { "component": "sensor" } ],
      "deployment": {                               // SOSA Deployment : le montage
        "id": "<mounting id>", "mounted_at": "…",
        "rotation_applied": { "theta_x": { "value": …, "unit": "deg" }, …, "convention": { … },
                              "origin": "calibrated | trial | ideal", "calibration_id": "… | null" }
      }
    },
    "conditioning": { "uses": [ { "component": "conditioning_electronics_board" } ] },
    "synchronous_detection": {
      "uses":  [ { "component": "signal_generation_chip", "channels": ["3", "4"] } ],
      "state": { "lock_in_enabled": true, "compensation_enabled": false,
                 "phase_offset": { "value": …, "unit": "deg" }, "phase_offset_origin": "calibrated | manual",
                 "phase_calibration_id": "… | null" }
    },
    "digitization": { "uses": [ { "component": "adc" }, { "component": "microcontroller" } ] },
    "positioning":  { "uses": [ { "component": "motors" } ] },   // SOSA Actuation
    "auxiliary_probes": { "uses": [ { "component": "electric_field_probe" } ] }
  },

  "data": {                                         // fichiers produits (PROV wasGeneratedBy)
    "files": [ { "name": "…_aefi.csv", "format": "CSV" }, … ],
    "columns": {                                    // SOSA observedProperty : sens + repère + unité
      "voltage_x_in_phase": { "observed_property": "electric field, in-phase component",
                              "axis": "x", "frame": "sensor", "unit": "V" },
      "x": { "observed_property": "position", "axis": "x", "frame": "bench", "unit": "mm" },
      "timestamp": { "observed_property": "result time", "unit": "ISO 8601 with offset" },
      …
    }
  },

  "warnings": [ { "path": "components.adc.characterization.noise", "message": "not characterized" } ]
}
```

### Avertissements

- Liste **unique** en fin de document. Chaque entrée : `path` (chemin JSON de la
  donnée concernée) + `message`.
- Émis pour : composant non monté, grandeur non caractérisée, réglage inconnu ou
  fichier illisible, rotation non calibrée (`origin` ≠ `calibrated`), arbre de
  travail modifié, calibration de phase absente alors que la compensation est
  active, `feature_of_interest.description` vide, acquisition non terminée
  (`ended_at` nul).

### Cycle de vie du document

Écrit au **démarrage** de l'acquisition (`status: running`, `ended_at: null`),
réécrit à la **fin** avec `ended_at`, `status` et `failure_reason`. Un document
resté `running` signale une acquisition interrompue (plantage).

### Inventaire des sources (ce que le garde-fou vérifie)

Chaque fichier de `config_templates/` et chaque registre de
`.aefi_acquisition/calibrations/` a une place, ou une exclusion motivée. Un
nouveau fichier sans ligne ici fait échouer la suite de tests.

| Source | Place dans le document |
|---|---|
| `ad9106_default_config.json` (+ `_last`) | `components.signal_generation_chip.settings` |
| `ads131a04_default_config.json` (+ `_last`) | `components.adc.settings` |
| `mcu_default_config.json` (+ `_last`) | `components.microcontroller.settings` |
| `arcus_default_config.json` + `motion_last_config.json` | `components.motors.settings` |
| `electric_field_probe_config.json` | `components.electric_field_probe.settings` |
| `scan_default_config.json` | `procedure.step_scan` (la config **utilisée**, venue du domaine `StepScanConfig`) |
| `aefi_device_config.json` | exclu : amorce historique. Ses parties vivantes sont migrées (géométrie → registre ; angles idéaux → `rotation_applied` avec `origin: ideal` ; identités → catalogue des composants) |
| `scan_config.json`, `export_default_config.json` | exclus : préférences d'interface (`UIConfigStore`), pas des paramètres de mesure |
| `acquisition_config.json`, `additional_sensors_config.json`, `bench_config.json` | exclus : lus par aucun code |
| registre des composants (`<kind>_calibration.json`, `hardware_components/`) | `components.<kind>.component` / `characterization` |
| `sensor_calibration.json` | `measurement_chain.sensor.deployment.rotation_applied` (l'entrée **appliquée**) |
| `source_geometry_calibration.json` | `measurement_chain.excitation.sources` (l'entrée **appliquée**) |
| `synchronous_detection_phase_calibration.json` | `measurement_chain.synchronous_detection.state.phase_calibration_id` |

État d'exécution sans fichier, à lire chez son service : mode et niveaux
d'excitation (`ExcitationConfigurationService`), rotation appliquée
(`SensorCalibrationService.get_active_rotation`), état de la détection synchrone
(`SynchronousDetectionService`), identité et batterie de la sonde, objet mesuré
et opérateur (saisis au lancement de l'acquisition).

### Standards de référence

| Notion du schéma | Standard |
|---|---|
| `components`, `uses`, `deployment`, `feature_of_interest`, `procedure`, `data.columns.*.observed_property`, actuation | W3C/OGC SOSA/SSN (2023, aligné ISO 19156) |
| `characterization` (+ `conditions`) | SSN System Capabilities (`SystemCapability`, `OperatingConditions`) |
| `provenance.activity` / `software` / `operator`, `data.files` | W3C PROV-O (`Activity`, `SoftwareAgent`, `Person`, `wasGeneratedBy`) |
| objets quantité `{value, unit}`, codes UCUM | QUDT `QuantityValue`, OGC SensorThings `unitOfMeasurement`, NeXus `@units` |
| unicité, propriétés dérivées, liens porteurs de métadonnées, forme commune des composants | Palantir Ontology (structural guidance, interfaces, object-backed links) |

Hors 1.0, gardés comme pistes : un `@context` JSON-LD reliant les clés à
SOSA/PROV/QUDT (structure inchangée, lisible par machine) ; orientation et
positions en chaîne `NXtransformations` (NeXus) ; un `ro-crate-metadata.json`
autour du dossier d'export pour le dépôt des données ; un HDF5 structuré NeXus.

### Ce qui change par rapport à 0.2-agile

| 0.2-agile | 1.0 |
|---|---|
| `metadata_schema_version` | `schema.version` |
| `acquisition_id` / `scan_id`, `acquisition_kind`, `generated_at` | `provenance.activity` + `provenance.generated_at` |
| — | `provenance.software`, `provenance.operator`, `activity.ended_at` / `status` |
| (nom du dossier) | `feature_of_interest` |
| `scan` | `procedure.step_scan` (+ `differential`, `measurement_uncertainty`, absents avant) |
| `export` (+ `units`) | `data` (`files`, `columns` : sens + repère + unité) |
| `excitation` | `measurement_chain.excitation.state` (déclaré dérivé) |
| `hardware_configuration.<kind>` + `hardware_settings.<chip>` | `components.<kind>` |
| `hardware_configuration.sensor_calibration_latest` | `measurement_chain.sensor.deployment.rotation_applied` |
| `hardware_configuration.source_geometry_latest` + `source_frame_reconstruction` | `measurement_chain.excitation.sources` |
| `motion_last_config` | `components.motors.settings` |
| `electric_field_probe`, `electric_field_probe_connection_defaults` | `components.electric_field_probe` |
| `hardware_configuration.warnings`, `hardware_settings.warnings` | `warnings` (liste unique, avec chemin) |
| — | `measurement_chain.synchronous_detection` |
| valeurs nues + tables d'unités séparées | objets quantité `{value, unit}` (UCUM) |
| dates locales sans fuseau / UTC mélangées | ISO 8601 avec décalage partout |

Pas de compatibilité avec 0.2-agile : aucun code ne lit ce fichier
(`aefi_post_processor_module` reçoit ses métadonnées autrement).

### Questions ouvertes

- **Saisie de l'objet mesuré et de l'opérateur** : un champ au lancement d'un
  scan et d'une série temporelle (vide autorisé, mais signalé). Mémoriser la
  dernière valeur saisie ?
- `aefi_device_config.json` contient deux faits physiques présents nulle part
  ailleurs : `sensor.position_relative_to_sources` et
  `sensor.counter_electrode_feedback_mode`. Les migrer dans le catalogue des
  composants (caractérisation du capteur), ou les déclarer obsolètes ?
- Fréquence du quartz de l'ADC (CLKIN) : absente partout. Sans elle, la cadence
  ADC ne se recalcule pas depuis l'OSR et les diviseurs — l'ajouter à la
  caractérisation du composant `adc` ?
- **Conditions de caractérisation** : le catalogue des composants n'enregistre
  pas encore sous quelles conditions (fréquence, température) une grandeur a été
  caractérisée. À ajouter au domaine quand un premier cas l'exige (gain de la
  carte de conditionnement en fonction de la fréquence ?).
