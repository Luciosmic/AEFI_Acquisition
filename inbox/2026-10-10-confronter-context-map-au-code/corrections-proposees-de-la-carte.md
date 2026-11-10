# Corrections proposées de la context map (2026-10-10)

17 corrections, dans l'ordre de la carte. Aucune n'est appliquée : la carte n'a pas été modifiée.
Les preuves sont dans `etat-des-contrats.md` et `dettes-d1-d3.md`. Les trois premières changent le sens de la carte, les autres sont des mises à jour.

## Corrections de fond

| # | Endroit de la carte | Écart | Formulation corrigée proposée |
|---|---|---|---|
| 1 | Titre du schéma, « Published Language : JSON enrichi DGP », et § 1 Exports | Acquisition n'a jamais écrit de bloc `dgp` avec `positions_m`, `radii_m`, `potentials_V` | « Acquisition exporte `*_acquisition-parameters.json`. La géométrie reconstruite y figure sous `hardware_configuration.source_frame_reconstruction` (`sphere_positions`, `sphere_radii`, clés `S1..S4`, positions 2D en mètres, depuis le 2026-10-01). L'excitation y figure sous `excitation` (`mode`, `level_s1_s2_percent`, `level_s3_s4_percent`, `frequency_hz`). Aucun potentiel par sphère n'est exporté. » |
| 2 | § 1, « Les consumers ne recalculent pas le DGP » ; claim extractible n° 4 | MCI recalcule le DGP depuis les mesures au pied à coulisse ; Acquisition le calcule aussi de son côté | « La reconstruction DGP est implémentée deux fois, dans Acquisition (`SourceFrameSolver`) et dans MCI (`dgp_reconstruction_service`). Aucun consommateur ne lit la reconstruction exportée par Acquisition. » À retirer des claims à miner tant que ce n'est pas vrai. |
| 3 | Schéma et § 2, « Conformist d'Acquisition » pour le Forward_Problem_Simulator | Ni MCI ni FEM ne lit un export d'Acquisition en production | « Relation visée : Conformist. Relation réelle : aucune intégration par fichier. MCI et FEM reprennent la géométrie par recopie (mesures au pied à coulisse dans un JSON de run MCI, sources codées en dur dans la config FEM). Seul l'ordre canonique des sphères est partagé. » |
| 4 | § 2, « Les deux implémentent le même port `IForwardSolver` » ; claim n° 2 | Le port n'existe pas, les deux signatures sont sans rapport | « MCI et FEM sont deux codes séparés. Un port commun `IForwardSolver` est une cible, pas un fait. » Le claim n° 2 est une décision d'architecture, pas un constat : à formuler comme telle. |
| 5 | § 2 Adaptateur FEM, « Consomme le .pos MCI comme champ de taille a priori » ; tableau, ligne 3, « Stable » | L'export existe, personne ne l'appelle. Le maillage de production suit l'indicateur DWR | « Champ de taille MCI a priori : écrit, non utilisé. Le maillage de production est adapté a posteriori par l'indicateur DWR. » Stabilité : « dormant ». |
| 6 | § 2, absent | Le contrat MCI → FEM réellement en service n'est pas dans la carte | Ajouter : « MCI → FEM, condition de Dirichlet exacte : le FEM impose sur la frontière de troncature le potentiel primaire MCI (`mci_exact_bc_function`). Dépendance de code directe, par `sys.path`, sur `SimulationConfig` et `StandardImageChargesCalculator` de MCI. » |
| 7 | § 3 Post_Processor, « agrège toutes les sources (mesures, MCI, FEM) », « Point d'entrée unique pour la comparaison modèle/mesure » | Le module ne lit que le CSV d'Acquisition. Les comparaisons modèle/mesure vivent dans les repos MCI et FEM | « Le Post_Processor traite les mesures seules (rotation vers le repère des sources, interpolation, soustraction du signal d'un point de référence, visualisation). La comparaison modèle/mesure est faite par des scripts des repos MCI et FEM. Rôle d'agrégateur : cible. » |
| 8 | Dette D1 | Localisation et énoncé faux (voir `dettes-d1-d3.md`) | « D1 — Le lecteur FEM `load_sphere_sources_from_dgp_json` attend un bloc `dgp` qu'aucun producteur n'émet. Résolution : lui faire lire `source_frame_reconstruction` et `excitation.mode` de l'export d'Acquisition. Dans MCI, `potentials_V` porte tantôt un signe, tantôt des volts : ne pas renommer globalement. » |

## Mises à jour

| # | Endroit de la carte | Écart | Formulation corrigée proposée |
|---|---|---|---|
| 9 | § 1 Repo | Chemin inexistant | `EXPERIMENTAL/AEFI_Acquisition/` |
| 10 | § 2 Repo | Chemins inexistants | MCI : `SIMULATIONS-NUMERIQUES/AEFI_Forward_Problem/AEFI_Mirror_Charges_Primary_Field_Calculator/`. FEM : `SIMULATIONS-NUMERIQUES/AEFI_Forward_Problem/AEFI_4Sphere/AEFI_4Sphere_firedrake/notebooks/NOTEBOOK_aefi_dwr/` |
| 11 | § 3 Repo, « à définir » | Le module existe | `EXPERIMENTAL/AEFI_Acquisition/external_modules/aefi_post_processor_module/` (dans le repo d'Acquisition, lancé depuis son tableau de bord) |
| 12 | § 4 Repo, « en initialisation » | Le dossier ne contient que des scripts d'identification de dipôles, sans lien avec la suite | « `SIMULATIONS-NUMERIQUES/AEFI_Inverse_Problem/` : scripts exploratoires isolés. Aucun contrat entrant. » |
| 13 | § 1, `excitation.mode (X_DIR / Y_DIR / Z_DIR)` | Pas de `Z_DIR` dans le code | `X_DIR`, `Y_DIR`, `CIRCULAR_PLUS`, `CIRCULAR_MINUS`, `CUSTOM` |
| 14 | § 1, « CSV/HDF5 `*_data` — champ E ou potentiels Uk » | Nom et contenu | « `<horodatage>_<scan>_aefi.csv` et `.h5` : tensions en phase et en quadrature par axe du capteur, avec écarts-types et ligne de base » |
| 15 | § 1, `sensor : calibration, rotation lab frame` | Clé déplacée | `hardware_configuration.sensor_calibration_latest` (dernière calibration enregistrée, pas nécessairement celle appliquée) |
| 16 | Tableau, ligne 1, « JSON (schema v0.1-agile) » ; dette D3 | Version et nom du champ | « `metadata_schema_version: "0.3-agile"` pour les scans. Un schéma 1.0 existe, branché seulement sur l'export de caractérisation de débit. » |
| 17 | § 2 Adaptateur MCI, « cache par hash de configuration, callable `mci_eval(pts)` » ; fichiers touchés de D1 (`SCRIPT_aefi_object_pipeline.py`) ; claim n° 3 | Le cache MCI indexe un champ normalisé sur grille, pas une évaluation ponctuelle ; `SCRIPT_aefi_object_pipeline.py` n'est plus qu'un réexport | « Cache SHA-256 du champ normalisé sur grille (`NormalizedPrimaryFieldService`). L'évaluation ponctuelle `(N,3) → (N,)` est `mci_potential`, côté FEM, sans cache. » Remplacer `SCRIPT_aefi_object_pipeline.py` par `scripts/config/aefi_config.py`. |

## Effet sur les claims à miner

Des cinq « claims extractibles » de la carte, un seul n'est pas contredit par le code : le n° 1 (invariance du maillage par V0), qui est un énoncé de physique que cette confrontation ne teste pas. Les n° 2 et 5 décrivent une cible, les n° 3 et 4 sont faux en l'état.
