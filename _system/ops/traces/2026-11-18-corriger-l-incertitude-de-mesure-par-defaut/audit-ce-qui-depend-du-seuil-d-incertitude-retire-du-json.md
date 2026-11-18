---
doc_type: audit
statut: to_validate
---

# Ce qui dépend du seuil d'incertitude retiré du JSON (schéma 1.5)

Décision de l'humain (2026-11-18) : option A, retirer `procedure.step_scan.measurement_uncertainty` du JSON.
Fait : sérialiseur, DTO d'export, service d'export, version 1.5, 6 tests, contrat du schéma (commits `93f1d420` et `6ee682bb` de `dev_post_processor`).
Ce document liste ce qui reste derrière, et ce que la carte des contextes peut en tirer.

## 1. Reste de la chaîne dans l'acquisition (hors du périmètre de A, à trancher)

Le seuil est toujours saisi, validé et stocké, mais plus rien ne le lit : il ne sort plus nulle part.

| Où | Ce qui reste |
|---|---|
| `src/interface/presenters/scan_presenter.py:217` | `uncertainty_volts=0.001  # Default`, la source du défaut |
| `src/application/scan/scan_application_service/dtos/scan_dtos.py:27` | champ `uncertainty_volts` du DTO de scan |
| `scan_application_service.py:1481-1483` | construit `MeasurementUncertainty` et logue ses avertissements |
| `src/domain/step_scan/value_objects/step_scan_config/step_scan_config.py:49` | `measurement_uncertainty` dans `StepScanConfig` (+ 5 fichiers de tests du domaine) |
| `src/domain/shared_kernel/value_objects/measurement_uncertainty/` | l'objet-valeur, son intention, son test ; `is_acceptable` n'a aucun appel |
| `src/application/shared/aefi_acquisition_service/dtos/aefi_acquisition_dtos.py:21`, `src/infrastructure/mocks/adapter_mock_i_aefi_acquisition_executor.py:62` | `target_uncertainty` appelle `configure_for_uncertainty`, définie seulement dans des tests (aucune définition dans `src/` hors tests) |

Recommandation : une seconde tâche, qui retire la chaîne entière (présenteur, DTO, config, objet-valeur, `target_uncertainty`). Elle dépasse 6 fichiers de `src/` : elle demande ton accord.

## 2. Consommateurs hors du dépôt

| Chemin | Ce qui dépend | Action proposée |
|---|---|---|
| `GRAPHE-THESE/_system/self/type/scan.type.yaml:16` | `measurement_uncertainty_max_V: Number{>0}`, champ **obligatoire** du type de motif de balayage, décrit « incertitude maximale admise » | le retirer, ou le rendre optionnel et le décrire comme seuil par défaut non appliqué ; toute configuration de scan écrite avec ce type porte aujourd'hui 0,001 |
| `PILOTAGE/_system/ops/traces/ontologie-des-donnees/2026-10-27-ecrire-la-couche-aefi/config-acquisition-traduite-pour-la-couche-aefi.yaml:24`, `…/2026-10-27-ecrire-le-package-sk-data/config-acquisition-exemple.yaml:31` | exemples avec `measurement_uncertainty_max_V: 0.001` | traces datées : on ne les réécrit pas, la correction vit dans le type |
| `PILOTAGE/…/2026-10-27-ecrire-le-package-sk-data/constat-blocs-en-attente-de-la-couche-aefi.md:17` | liste le champ du bloc `scan` | idem |
| `SOLIDKNOWLEDGE-PACKAGES/sk-data/_system/ops/traces/sk-data-pour-l-experimental-et-le-mode-manuel/2026-11-09-remplacer-l-axe-par-la-plage/constat-configs-a-migrer-hors-de-sk-data.md` | cite le champ | trace datée, idem |
| `AEFI-THESIS-DATA-EXPERIMENTAL/acquisitions/2026-11-13_204052_*_acquisition-parameters.json` | schéma 1.4, porte 0,001 V | donnée publiée : on ne la modifie pas ; le contrat dit désormais que les fichiers 1.0 à 1.4 ne se lisent pas comme une mesure |

Le post-traitement n'est pas concerné : il ne lit que la grille et la version (`acquisition_parameters_translator.py`), et lit `1.5` sans changement.

## 3. Ce que la carte des contextes peut gagner

À ajouter à `_system/documentation/context-map-acquisition-post-traitement.md`, après ton accord :

1. **Section 2, « Ce que le post-traitement attend du fichier »** : dire en face de chaque champ du fichier qui le lit, aujourd'hui (grille, version, `rotation_applied` en tranche 2). Un champ que personne ne lit se voit alors tout de suite, et celui-ci serait apparu comme tel.
2. **Section 7, « Qui change quand »** : ajouter la ligne « champ retiré du fichier des paramètres » (ici : version mineure, car aucun lecteur ; sinon version majeure annoncée au client). La ligne existante ne couvre que l'ajout.
3. **Une section sur les lecteurs hors des deux logiciels** : le type `scan` de GRAPHE-THESE et ses configurations reprennent des champs de l'acquisition. Le seuil y est entré parce qu'un champ du logiciel a été traduit tel quel, sans demander s'il était mesuré. C'est un lien non cartographié, du fournisseur (l'acquisition) vers la couche de données.
4. **Règle à poser** : un champ exporté dit s'il est mesuré, demandé ou défaut. C'est celle que le seuil enfreignait.

## Questions

1. Retirer la chaîne entière du seuil dans l'acquisition (section 1), en seconde tâche ?
2. Corriger `scan.type.yaml` dans GRAPHE-THESE (retrait ou champ optionnel) ?
3. Écrire les 4 ajouts de la section 3 dans la carte des contextes ?
