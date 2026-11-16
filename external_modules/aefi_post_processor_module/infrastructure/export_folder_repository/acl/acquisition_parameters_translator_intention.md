---
type: traducteur-anti-corruption::solidai-hexagonal
tldr: "Traduire le fichier des paramètres d'une acquisition (le contrat de l'acquisition) en ce que le catalogue montre : type de scan, date de début, objet mesuré, lift-off, version du schéma."
code: ["[[external_modules/aefi_post_processor_module/infrastructure/export_folder_repository/acl/acquisition_parameters_translator.py]]"]
cause_de_changement: outil
part_of: "[[external_modules/aefi_post_processor_module/infrastructure/export_folder_repository/export_folder_repository_intention]]"
---
# acquisition_parameters_translator — Intention

## Rationale

Le nom d'un dossier d'acquisition se renomme à la main et n'a pas de version : un catalogue qui en tire l'objet mesuré ou le lift-off affiche ce qu'un nom mal formé lui fait croire.
Le fichier des paramètres d'acquisition est le contrat client-fournisseur entre l'acquisition et le post-traitement (carte des contextes, § 2) : il porte sa version de schéma et décrit l'acquisition.
Sans traducteur, le dépôt des acquisitions lirait directement la forme JSON du fournisseur, et chaque évolution du schéma toucherait le parcours du disque.

## Responsibility

- `describe(parameters)` : du contenu JSON du fichier, rendre une `ParametersDescription` :
  - `kind` : `flyScan` pour `fly_scan`, `stepScan` pour `step_scan` à partir du schéma 1.4 ; `None` pour un `step_scan` plus ancien, où un scan au vol était aussi déclaré `step_scan` ; `NOT_A_SCAN` pour une autre activité (série temporelle, balayage en fréquence) ;
  - `acquired_at` : le début de l'activité (`provenance.activity.started_at`), avec son fuseau ;
  - `measured_object` : la description de l'objet mesuré (`feature_of_interest.description`) ;
  - `lift_off_mm` : la grandeur de `feature_of_interest` dont l'alias est `lift_off`, en millimètres ;
  - `schema_version`.
- Un champ absent ou mal formé donne `None`, jamais une exception : un export ancien reste listé.

## Design

- Fonction pure sur un `dict` : le dépôt lit le fichier, le traducteur ne fait aucune entrée-sortie.
- Le lift-off se reconnaît par son alias, pas par le nom long de la grandeur, et doit être en `mm`.
- Seul `export_folder_repository` l'appelle.
