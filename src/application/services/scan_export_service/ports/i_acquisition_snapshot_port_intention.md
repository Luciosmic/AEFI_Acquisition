# i_acquisition_snapshot_port — Intention

## Rationale

Une partie des conditions matérielles vit dans des registres domaine
(catalogue des composants, calibrations), une autre dans des fichiers de
config sur disque (AD9106, ADS131A04, MCU résolus `default + last`). Il fallait
un seul endroit qui les rassemble, sans que le code qui les consomme connaisse
les noms et formats de fichiers.

## Responsibility

- Une requête en lecture seule, `read()`, qui rend ces faits sous forme de
  dict (`hardware_configuration`, `hardware_settings`, …).
- Ne jamais lever : une source absente ou illisible devient un avertissement,
  pas une exception.

## Design

- ABC pure. Implémenté par `infrastructure/persistence/acquisition_snapshot_reader.py`.
- Depuis le 2026-10-02, son seul consommateur est
  `infrastructure/acquisition_conditions/acquisition_conditions_reader.py`,
  qui le traduit en `AcquisitionConditionsDTO` pour tous les exports
  (`IAcquisitionConditionsPort`). `ScanExportService` ne le lit plus.
  `ponytail:` le port reste dans le dossier du service d'export alors qu'il ne
  sert plus qu'entre deux adaptateurs ; à déplacer en infrastructure le jour où
  il change.
