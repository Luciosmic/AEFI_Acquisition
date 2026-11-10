# Architecture présente dans le code et absente de la carte (2026-10-10)

8 éléments. Abréviations : `ACQ/`, `MCI/`, `FEM/` comme dans `etat-des-contrats.md` ; `FP/` = `SIMULATIONS-NUMERIQUES/AEFI_Forward_Problem/`.

## Contrats et dépendances non déclarés

1. **MCI → FEM par condition aux limites exacte.**
   Le FEM impose le potentiel primaire MCI sur la frontière de troncature : `FEM/scripts/fem/aefi_water_cylinder_scan_solvers.py:24,52`, `FEM/scripts/fem/aefi_mci_exact_bc.py:43-74`.
   C'est le seul couplage MCI/FEM utilisé par les scripts de production (`run_water_cylinder_scan_point.py:76`, `run_water_cylinder_scan_uniform.py:106`, `study_water_cylinder_jc_convergence.py:99`).

2. **Dépendance de code FEM → MCI par `sys.path`.**
   `FEM/scripts/fem/aefi_mci_exact_bc.py:26-35` remonte six niveaux de dossiers et ajoute `MCI/` au chemin d'import pour utiliser `SimulationConfig`, `StandardImageChargesCalculator` et `COULOMB_K`.
   Un déplacement de dossier ou un renommage dans le domaine MCI casse le FEM sans avertissement. En termes de context map : un Shared Kernel de fait, sans paquet ni version.

3. **Le gabarit `aefi_device_config.json` comme second langage publié.**
   `ACQ/config_templates/aefi_device_config.json` (`schema_version: "3.0"`) est lu par le Post_Processor (`composition_root.py:44-51`), par le simulateur fictif d'Acquisition (`ACQ/src/infrastructure/mocks/point_charge_field_simulator.py:41`) et prévu côté MCI avec contrôle de version (`MCI/domain/aefi_device/aefi_device.py:139-160`).
   La carte ne parle que de l'export par scan. Ce fichier de configuration est versionné et vérifié, ce que l'export n'est pas.

4. **Données de mesure copiées dans les repos de simulation.**
   `FEM/experimental_data/2026-07-29_175721_stepScan_…/` contient une copie d'un export d'Acquisition, lue par `FEM/scripts/extract_experimental_profile_y635.py:19`.
   MCI lit des mesures Narda par chemin absolu vers un dossier qui n'existe plus à cet endroit : `MCI/execute_pipeline_narda_primary_field_comparison.py:87-91` (`1 - THESE/0_inbox/data-a-interpreter/…`).
   Le flux Acquisition → simulation passe donc par copie manuelle de dossiers, pas par un contrat.

## Contextes et responsabilités non cartographiés

5. **La comparaison modèle/mesure vit dans les repos de simulation.**
   Côté MCI : `MCI/execute_pipeline_narda_primary_field_comparison*.py`, `execute_pipeline_narda_order_comparison.py`. Côté FEM : `FEM/scripts/compare_experimental_profile_y635_rotation_trios.py`, `compare_water_cylinder_scan_rotations.py`.
   C'est le rôle que la carte attribue au Post_Processor.

6. **`AEFI_Primary_Field_Comparator`.**
   `FP/AEFI_Primary_Field_Comparator/src/` : application en couches (domaine, service de comparaison, lecteurs COMSOL et NetCDF) qui compare des champs primaires de plusieurs solveurs. Absent de la carte, alors que c'est un agrégateur de sorties de solveurs.

7. **Autres solveurs du problème direct.**
   `FP/AEFI_4Sphere/` contient aussi `AEFI_4Sphere_simulator_app/` (application hexagonale, repo git propre, solveur COMSOL, port `IJobExecutor` dans `src/application/ports/i_job_executor.py:21`), `AEFI_4Sphere_comsol/`, `_fenics/`, `_julia/`, et à côté `AEFI_VIE/`, `AEFI_Born_PSF_Calculator/`, `AEFI_Uniform_Field_PSF/`.
   La carte ne retient que MCI et FEM Firedrake et cite `AEFI_Simulator_App` comme simple nom de cible. Le simulator_app a déjà un port de substitution de solveur : candidat naturel à comparer à `IForwardSolver` avant d'en écrire un nouveau.
   Dans le repo Firedrake lui-même, deux arborescences en couches coexistent avec les scripts de `notebooks/` : `AEFI_4Sphere_firedrake/src/` (port `IFemSolver`, `src/application/simulation_service/ports/i_fem_solver.py:18`) et `AEFI_4Sphere_firedrake/aefi_firedrake_simulator/`. Leur lien avec le pipeline `NOTEBOOK_aefi_dwr` n'a pas été établi ici.

8. **Sous-domaine Calibration dans Acquisition.**
   `ACQ/src/domain/calibration/` porte la géométrie des sources (`SourceFrameSolver`, `source_frame_solver.py:75-77`), la calibration du capteur et le catalogue des composants matériels. C'est lui, et non un « enrichissement DGP » du JSON, qui produit ce que les simulateurs devraient consommer.
   Autres modules d'Acquisition hors carte : `ACQ/external_modules/electric_field_probe_post_processor/` (post-traitement de la sonde Narda), et les services de caractérisation de débit, seuls à écrire le schéma 1.0.

## Non exploré

- `SIMULATIONS-NUMERIQUES/AEFI_Banc_Test_II/` et `EXPERIMENTAL/AEFI_Data/` : non ouverts.
- `ACQ/external_modules/post_processor_module/` et `cube_visualizer/` : restes sans code actif d'après le README du dossier, non vérifié fichier par fichier.
