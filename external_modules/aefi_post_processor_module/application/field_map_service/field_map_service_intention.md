---
type: service-applicatif::solidai-hexagonal
tldr: "Dire quelles étapes une acquisition a rangées et rendre une étape en carte : une grille 2D par canal et l'étendue."
code: ["[[external_modules/aefi_post_processor_module/application/field_map_service/field_map_service.py]]"]
cause_de_changement: orchestration
ports: 
  - ^: i-api-field-map-service
    type: port::solidai-hexagonal
    tldr: "list_steps et load_step : les étapes rangées d'une acquisition, et une étape en carte."
    sens: entrant
    code: "[[external_modules/aefi_post_processor_module/application/field_map_service/i_api_field_map_service.py]]"
  - ^: i-step-reader
    type: port::solidai-hexagonal
    tldr: "list_steps et read_step : les étapes d'un fichier d'acquisition et la lecture brute d'une étape."
    sens: sortant
    code: "[[external_modules/aefi_post_processor_module/application/field_map_service/ports/i_step_reader.py]]"
---
# field_map_service — Intention

## Rationale

La fenêtre à panneaux montre une étape calculée comme une carte. Le modèle de l'ancienne fenêtre mêlait la lecture du fichier HDF5, le décodage des métadonnées (noms de canaux et étendue stockés en JSON ou en tableau) et la mise en grilles. Sans service, le panneau Carte rouvrirait h5py et refaisait ces décodages.

## Responsibility

- `list_steps(StepsRequestDTO)` : les étapes rangées, dans l'ordre du traitement, aucune si le fichier manque ou est illisible.
- `load_step(LoadStepDTO)` : une `FieldMapDTO`, une grille 2D par canal et l'étendue `[gauche, droite, bas, haut]`.
- Retomber sur les six canaux de tension quand les noms manquent ou ne correspondent pas aux données, et sur l'étendue `[0, 1, 0, 1]` sans étendue, en le journalisant.

## Design

- Le lecteur d'étapes est un port sortant en lecture seule ; le service décode, l'adaptateur rend les étapes telles que rangées.
- Même résultat que `VisualisationModel.get_step_data` de l'ancienne fenêtre, comparé dans `_tests/acquisition_catalog_and_field_map_test.py`.
