---
doc_type: decoupage
type: constat::sh-agent-os
genere_par: "[[tache - tranche 2 partie 1 angles appliques et panneau parametres]]"
---

# Découpage de la tranche 2 (lecture des paramètres d'acquisition)

Modèle : `decoupage-de-la-tranche-1.md`. Pourquoi : le fichier `<acquisition>_acquisition-parameters.json` est un contrat client-fournisseur (post-traitement client, acquisition fournisseur) ; la carte des contextes (§ 6) relève deux écarts, que l'humain a tranchés le 2026-11-16. Les étapes 2.0 à 2.7 sont la **partie 1** (cette délégation, tout dans le module) ; 2.8 à 2.11 sont la **partie 2** (plus tard, elles touchent `src/` et attendent qu'une autre session commite ses fichiers d'export).

## Décision de conception de la partie 1

- Les paramètres entrent par le chemin du catalogue, comme l'objet mesuré et le lift-off : traducteur du dépôt (`export_folder_repository/acl`) → `AcquisitionRecord` → `AcquisitionStatusDTO` → presenter. Un seul lecteur du fichier pour le catalogue ; `IScanPlanReader` et son adaptateur ne changent pas (la grille prévue reste son affaire).
- Le **service de traitement décide** : `ProcessScanDTO` gagne `applied_rotation_angles` (primitives, `None` par défaut) ; si elles sont données, elles remplacent `parameters.rotation_angles` ; sinon rien ne change (les scans de l'étalon n'ont pas de fichier de paramètres). Le presenter transmet ce que le catalogue a lu, sans décider. Le chemin de l'acquisition (adaptateur de `src/` → `ProcessingPipeline`) n'envoie pas ce champ : il garde ses propres angles, qui sont ceux de la calibration active, donc ceux du fichier.
- `RotationConvention` est **empruntée** : `aefi_acquisition_upstream/upstream_calibration.py` la réexporte (second fichier, parce que `upstream_objects.py` tire Qt et le câblage sans Qt ne doit pas le charger). Seul le traducteur l'importe, pour **refuser** une convention que l'application ne sait pas appliquer (écart 7 de l'avis) ; le domaine et l'application gardent la convention en trois chaînes.
- `applies_to_data: true` (valeurs exportées déjà tournées) est refusé comme une convention inconnue : tourner deux fois serait faux. Absent ou `false` : on tourne (l'export du CSV est toujours dans le repère du capteur).
- Un refus ne fait pas échouer l'acquisition : pas d'angles appliqués, `rotation_problem` dit pourquoi (affiché dans le panneau et dans le journal), le traitement retombe sur les angles idéaux, comme aujourd'hui.

## Commandes d'acceptation de référence

Depuis la racine du checkout (`export UV_PROJECT_ENVIRONMENT=~/.venvs/AEFI_Acquisition QT_QPA_PLATFORM=offscreen`) :
- `V1` : `uv run pytest external_modules/aefi_post_processor_module -q`
- `V2` : `~/.venvs/solidai-verify/bin/solidai verify --entry . --target external_modules/aefi_post_processor_module`
- `V3` : `uv run pytest src/infrastructure/aefi_post_processor_port src/application/scan/scan_application_service/_tests/scan_export_with_post_processing_integration_test.py -q`

Base mesurée à `develop` (5a6da203), le 2026-11-19 : `V1` = 170 réussis et 2 échecs connus (`test_offset_removal`, `test_phase_recovery`, 180°, tranche 5) ; `V2` = 0 erreur, 46 vérifications ; `V3` = 6 réussis. Chaque étape de la partie 1 laisse `V1` à ces 170 plus ses nouveaux tests, les mêmes 2 échecs, `golden_master_test` vert sans toucher à `_tests/golden/`, `V2` à 0 erreur, `V3` à 6.

## Partie 1 (cette délégation)

### 2.0 — Préparation (pas de commit de code)
Relever `V1`, `V2`, `V3`, écrire le découpage, ajouter les étapes au plan.
**Test d'acceptation :** les trois relevés (`pytest-v1-base.log`, `solidai-verify-v2-base.log`, `pytest-v3-base.log`) et ce fichier sont dans la trace ; le plan porte `etape-2-0` à `etape-2-11`.

### 2.1 — Le domaine : la rotation appliquée
`domain/acquisition_record/value_objects/applied_rotation/` (D3, `value-object`, `part_of` la racine, immuable) : trois angles en degrés, convention en trois chaînes (`type`, `order`, `direction`), `origin` et `calibration_id` facultatifs. `AcquisitionRecord` gagne `applied_rotation`, `rotation_problem` et `schema_version` (tous `None` par défaut : le catalogue existant ne change pas). Intention du VO, intention de la racine mise à jour (elle annonçait « le refus d'une convention » pour la tranche 2).
**Test d'acceptation :** test du VO (immuable, `angles` en tuple) ; `acquisition_record_test` inchangé et vert ; `V2` = 0 erreur (D3, D5, D8).

### 2.2 — Le traducteur lit `rotation_applied` et emprunte la convention
`aefi_acquisition_upstream/upstream_calibration.py` réexporte `RotationConvention` ; l'intention de l'emprunt la liste. `acquisition_parameters_translator.describe` rend en plus `applied_rotation` et `rotation_problem` : lit `measurement_chain.sensor.deployment.rotation_applied` (`theta_x|y|z` `{value, unit: deg}`, `convention`, `origin`, `calibration_id`, `applies_to_data`) ; `RotationConvention(...)` valide la convention ; refus (`applies_to_data: true`, convention absente ou non prise en charge, angle manquant ou hors `deg`) = `None` + la raison. Intention du traducteur mise à jour (une seule raison de changer : la forme du contrat).
**Test d'acceptation :** le test du traducteur lit une description complète (angles du scan de la bouteille d'eau : 34,9 ; 45,7 ; −5,3), une description sans déploiement (`None`, pas de problème), une convention `intrinsic` (`None` + raison), `applies_to_data: true` (`None` + raison), une unité `rad` (`None` + raison) ; `architecture_test` vert (le domaine et l'application n'importent pas `aefi_acquisition_upstream`) ; un test de l'import sans Qt (`import aefi_post_processor_module.infrastructure.export_folder_repository.acl.acquisition_parameters_translator` ne charge pas `PySide6`).

### 2.3 — Le catalogue porte la rotation, la version et le refus
`ExportFolderRepository` renseigne `applied_rotation`, `rotation_problem`, `schema_version` du record ; `AcquisitionStatusDTO` gagne `applied_rotation` (`AppliedRotationDTO` gelé, primitives), `rotation_problem`, `schema_version`, remplis par `AcquisitionCatalogService`. Le journal du dépôt dit le refus (`catalog.rotation_refused scan=… reason=…`).
**Test d'acceptation :** le test du dépôt (suite de contrat partagée avec le Fake) : un dossier avec fichier de paramètres complet rend les angles ; sans fichier, `None` partout, mêmes états qu'avant ; le catalogue rend le DTO ; `acquisition_catalog_and_field_map_test` vert ; aucun fichier créé ni modifié.

### 2.4 — Le retraitement utilise les angles appliqués
`ProcessScanDTO.applied_rotation_angles` (défaut `None`) ; `PostProcessingService` : angles du fichier si présents, sinon `parameters.rotation_angles`, journal `pipeline.rotation_source scan=… source=acquisition_parameters|request|none angles_deg=…` ; `AcquisitionsPresenter._process_one` transmet `status.applied_rotation.angles` quand il existe et journalise la source (`scan.processing … rotation_source=…`). `composition_root.py` : le `ponytail:` des angles idéaux est remis à jour (les angles idéaux restent le repli).
**Test d'acceptation :** test du service avec Fakes : avec `applied_rotation_angles=(34.9, 45.7, -5.3)` et `parameters.rotation_angles=(35.3, 45, 0)`, l'étape `rotated_frame` et ses métadonnées portent (34.9, 45.7, −5.3) ; sans le champ, identique à aujourd'hui ; test du presenter : une acquisition dont le fichier donne des angles les transmet au service, une sans fichier transmet `None` et garde les angles idéaux ; **`golden_master_test` vert sans modifier `_tests/golden/`** (preuve que les scans sans description n'ont pas bougé) ; `V3` = 6.

### 2.5 — Le panneau « Paramètres d'acquisition »
`interface/acquisition_parameters_presenter/` (typé `presenter`, `appelle` le catalogue, `vues` le panneau, sans Qt, sans domaine) et `interface/acquisition_parameters_panel/` (vue humble, sans type : objet mesuré, angles appliqués, convention, version du schéma, raison d'un refus ; lecture seule, aucun bouton qui écrit). `AcquisitionsPresenter.when_acquisition_selected(listener(status))` donne le statut choisi (il existe déjà `when_acquisition_chosen(name, fichier)` pour la Carte, inchangé). Textes : « non renseigné » quand le fichier ne dit rien.
**Test d'acceptation :** test du presenter avec une vue Fake : sélection d'une acquisition avec rotation appliquée → objet, trois angles avec leur unité, convention `extrinsic ZYX sources_to_sensor`, version ; sans fichier → « non renseigné » partout ; avec refus → la raison ; rien n'est écrit (liste des fichiers identique avant et après) ; test de la vue (`QT_QPA_PLATFORM=offscreen`) : les champs montrent ce que le presenter a posé.

### 2.6 — Le panneau dans la fenêtre à panneaux
`shell_wiring.py` construit le presenter et le panneau, ajoute `PanelSpec("acquisition_parameters", "Paramètres d'acquisition", "Données", …)` et l'abonne à l'Acquisitions ; `Shell` garde le presenter vivant. Intentions du câblage mises à jour.
**Test d'acceptation :** `shell_wiring_test` : la fenêtre porte quatre panneaux dont celui-ci ; `launch_test` (sous-processus offscreen, ligne `window.shown panels=[…'acquisition_parameters'…]`) ; sélectionner une acquisition dans la fenêtre assemblée met à jour le panneau.

### 2.7 — Documents, vérification d'ensemble, capture
`README.md` et `Data Processing Architecture.md` du module (le chemin des angles), plan (« Prochaine action » : partie 2), lancement offscreen sur une copie de l'acquisition de démonstration à laquelle on ajoute un fichier de paramètres avec `rotation_applied`, capture des valeurs du panneau, `V1`, `V2`, `V3` rejoués.
**Test d'acceptation :** les relevés finaux sont dans la trace ; `git diff` des commits de la partie 1 ne touche rien hors de `external_modules/aefi_post_processor_module/` et de `_system/ops/traces/post-traitement-conforme/`.

## Partie 2 (plus tard, après le commit des fichiers d'export de l'autre session)

### 2.8 — Retirer `Hdf5ScanExportPort` de l'export de l'acquisition (`src/`, branche `feature/*` depuis `develop`)
Le service d'export n'écrit plus de `.h5` ; il déclenche le traitement sur le seul CSV. **Test :** le test d'intégration d'export produit les CSV et le fichier de paramètres, aucun `.h5` brut ; `V3` mis à jour.

### 2.9 — Le post-traitement crée le `.h5`
`Hdf5StepWriter` crée le fichier s'il n'existe pas, y range les données brutes relues du CSV (`record_source` écrit déjà le CSV source), ses cinq étapes et la provenance : CSV source, son SHA-256 (à comparer à celui du fichier des paramètres), `provenance.activity.id`. À revérifier : les attributs de configuration de l'ancien `.h5` sont tous dans le fichier des paramètres. **Test :** un retraitement depuis le seul CSV reconstruit le `.h5` complet ; les valeurs des étapes de l'étalon n'ont pas bougé.

### 2.10 — Relever la version mineure du schéma
`data.files` ne liste plus de `.h5` : version mineure relevée dans le sérialiseur de l'acquisition, avec son test et son intention. **Test :** `acquisition_parameters_v1_test` sur la nouvelle version ; le traducteur lit l'ancienne et la nouvelle.

### 2.11 — Documents et vérification d'ensemble de la tranche 2
Carte des contextes (§ 6 : les deux écarts passent en « corrigés »), `README`, plan ; `V1`, `V2`, `V3`, `solidai verify --entry . --target .` comparé à `develop`. L'humain relance sur ses vraies acquisitions.
