# i_acquisition_snapshot_port — Intention

## Rationale

Le document de paramètres d'acquisition doit contenir ce que le système sait au
démarrage d'une acquisition : composants montés et leur caractérisation,
calibrations, réglages appliqués aux puces. Une partie vit dans des registres
domaine, une autre dans des fichiers de config sur disque (AD9106, ADS131A04,
MCU, moteurs n'ont pas tous de getter en mémoire). Sans ce port,
`ScanExportService` lirait ces fichiers lui-même — de l'I/O directe dans la
couche application, et un service couplé aux noms et formats de fichiers.

## Responsibility

- Une requête en lecture seule, `read()`, qui rend les sections de contexte
  matériel du document de paramètres, sous forme de dict prêt pour JSON.
- Ne jamais lever : une source absente ou illisible devient un avertissement
  dans le document, pas une exception (l'export ne doit pas échouer pour ça).

## Design

- ABC pure, sans état ni étape de configuration.
- Le contenu et l'organisation des sections suivent le schéma de référence
  `../acquisition_parameters/acquisition_parameters_intention.md`. État actuel
  (`0.3-agile`) : `hardware_configuration`, `hardware_settings`,
  `motion_last_config`, `electric_field_probe_connection_defaults` ; la
  migration vers 1.0 (`components` / `measurement_chain`) changera la forme du
  retour, pas le rôle du port.
- Implémenté par `infrastructure/persistence/acquisition_snapshot_reader.py`.
