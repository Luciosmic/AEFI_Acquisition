# Architecture du post-traitement AEFI

Le post-traitement transforme le CSV d'un scan en cinq étapes calculées, rangées dans le `.h5` de l'acquisition, et les montre dans une fenêtre à panneaux.
Il suit les couches de l'acquisition. Le détail de chaque atome est dans son `<nom>_intention.md`, à côté de son code.

## Couches

```mermaid
flowchart TB
    subgraph interface["interface/"]
        shell["shell/ : fenêtre, câblage, headless_wiring"]
        panels["panneaux Acquisitions, Carte, Logs + leurs presenters"]
    end
    subgraph application["application/"]
        catalog["acquisition_catalog_service"]
        process["post_processing_service"]
        fieldmap["field_map_service"]
    end
    subgraph domain["domain/"]
        record["acquisition_record : l'état d'une acquisition"]
        calc["processing/ : grid_builder, phase_calibrator, amplitude_subtractor, frame_rotator, interpolator, processing_steps"]
    end
    subgraph infra["infrastructure/"]
        repo["export_folder_repository"]
        reader["csv_scan_reader"]
        writer["hdf5_step_writer"]
        stepreader["hdf5_step_reader"]
        logging["logging"]
    end
    panels --> catalog & process & fieldmap
    catalog --> record
    process --> calc
    repo -.implémente.-> record
    reader -.implémente.-> process
    writer -.implémente.-> process
    stepreader -.implémente.-> fieldmap
```

Le sens des dépendances : l'interface et l'infrastructure importent l'application, l'application importe le domaine, le domaine n'importe que la bibliothèque standard et numpy/scipy. `_tests/architecture_test.py` le vérifie (ni `PySide6`, `pandas`, `h5py`, `pathlib`, ni l'acquisition dans `domain/` et `application/`).
`aefi_acquisition_upstream/` est le seul endroit qui emprunte du code à `src/` (fenêtre à panneaux, barre de tâches) : il règle `sys.path` et liste ce qu'il emprunte.

## Les cinq étapes

| Étape | Atome (`domain/processing/`) | Ce qu'il fait |
|---|---|---|
| `preprocessed` | `grid_builder` | CSV d'un scan, même incomplet, en grille carrée complétée de NaN, avec l'étendue |
| `phase_calibrated` | `phase_calibrator` | angle moyen θ = mean(atan2(Q, I)) sur le bord, rotation de −θ de toute l'image |
| `amplitude_subtracted` | `amplitude_subtractor` | moyenne du bord (NaN ignorés) retranchée à tous les pixels |
| `rotated_frame` | `frame_rotator` | rotation par quaternion du repère du capteur au repère des sources, angles de montage P = Rx·Ry·Rz |
| `interpolated` | `interpolator` | grille plus fine, `linear`, `cubic` ou `nearest`, NaN respectés |

Les noms et l'ordre sont fermés dans `processing_steps` ; les paramètres (largeur du bord, méthode, taille de grille, point de référence, angles) y sont gelés.

## Traiter une acquisition

```mermaid
sequenceDiagram
    actor Opérateur
    participant P as AcquisitionsPresenter
    participant C as acquisition_catalog_service
    participant S as post_processing_service
    participant R as csv_scan_reader
    participant W as hdf5_step_writer
    Opérateur->>P: bouton « Traiter »
    P->>C: list_acquisitions (état de chacune)
    loop chaque acquisition à recalculer
        P->>S: process_scan(csv, fichier d'étapes, paramètres)
        S->>R: lire le CSV
        loop cinq étapes
            S->>S: calcul du domaine
            S->>W: ranger l'étape
        end
        P->>C: report_outcome (réussite, ou étape fautive et message)
    end
    P->>P: bilan dans le journal, liste réaffichée
```

Une acquisition qui échoue ne stoppe pas les suivantes ; son échec nomme l'étape fautive.
Le fichier d'étapes est le `.h5` de l'acquisition (`processing_store_path`, un seul endroit à changer quand les étapes iront dans un fichier propre, tranche 6).

## L'état d'une acquisition

`AcquisitionRecord` décide, sans rien écrire :
- **à recalculer** si le fichier d'étapes manque, s'il ne contient pas `preprocessed`, si le CSV est plus récent que le fichier d'étapes, ou si le recalcul est forcé ;
- **traitée** sinon ;
- **en échec** pour une acquisition dont le traitement a échoué dans la session, avec son message.

Le catalogue liste ces états à l'ouverture et n'écrit aucun fichier : c'est ce que garde `_tests/launch_test.py`, en lançant la fenêtre dans un processus neuf.

## Structure du `.h5`

```
<acquisition>.h5
├── /preprocessed          data [N×N×6], attrs : extent, grid_size, channel_names, timestamp
├── /phase_calibrated      data [N×N×6], attrs : phase_angles, timestamp
├── /amplitude_subtracted  data [N×N×6], attrs : mean_amplitudes, timestamp
├── /rotated_frame         data [N×N×6], attrs : rotation_angles, quaternion, rotation_matrix, timestamp
└── /interpolated          data [M×M×6], attrs : interpolation_method, quality_metrics, timestamp
```

Les six canaux sont les tensions en phase et en quadrature de x, y et z.

## Tests

- **Étalon** (`_tests/golden_master_test.py`) : trois scans synthétiques traités par le service, chaque étape comparée octet pour octet à `_tests/golden/` (`np.array_equal`, NaN égaux). Il ne change qu'avec une décision sur les chiffres.
- **Atomes** : chaque dossier de `domain/processing/` a son `_tests/`, avec des fonctions analytiques à résultat connu (phase décalée, fond constant, rotation, convergence O(h²) en linéaire et O(h⁴) en cubique, grille incomplète).
- **Adaptateurs** : chaque adaptateur a son Fake et une suite de contrat que le réel et le Fake passent.
- **Presenters** : testés avec une vue Fake, le vrai catalogue et le vrai service sur des Fakes.
- **Lancement** (`_tests/launch_test.py`) : `composition_root.py` en sous-processus, Qt hors écran.
- **Côté acquisition** : `src/infrastructure/aefi_post_processor_port`, `scan_export_with_post_processing_integration_test.py` et `external_modules_panel_test.py` figent l'appel de l'adaptateur et le fichier produit.

Deux tests de calcul échouent depuis avant la refonte (écart de 180° sur x et y : `test_phase_recovery`, `test_offset_removal`) ; ils attendent la tranche 5.

## Diagrammes

`diagrams/class_diagrams.puml` (classes des couches), `diagrams/test_*.puml` (stratégie de test analytique). `diagrams/sequence_diagrams.puml` décrit l'analyse du bruit, pas le post-traitement.
