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
  - `schema_version` ;
  - `applied_rotation` : la rotation que l'acquisition a réellement appliquée (`measurement_chain.sensor.deployment.rotation_applied` : trois angles `theta_x|y|z` en degrés, convention, origine, identifiant de calibration), en `AppliedRotation` ;
  - `rotation_problem` : pourquoi une rotation décrite n'est pas utilisable, en une phrase. Sont refusés : une convention que `RotationConvention` (empruntée à l'acquisition) ne prend pas en charge ou absente, des valeurs déjà tournées (`applies_to_data: true` : les tourner encore serait faux), un angle absent, illisible ou dans une autre unité que le degré. Un fichier sans montage du capteur ne donne ni rotation ni problème.
- Un champ absent ou mal formé donne `None`, jamais une exception : un export ancien reste listé.

## Design

- Fonction pure sur un `dict` : le dépôt lit le fichier, le traducteur ne fait aucune entrée-sortie.
- Le lift-off se reconnaît par son alias, pas par le nom long de la grandeur, et doit être en `mm`.
- Seul `export_folder_repository` l'appelle.
- Il importe `RotationConvention` par `aefi_acquisition_upstream/upstream_calibration.py` : la convention a une seule définition, celle de l'acquisition, et le refus d'une convention inconnue est celui de l'acquisition. Le domaine n'en reçoit que trois chaînes. Un test charge le traducteur dans un processus neuf et vérifie que PySide6 n'est pas importé.
