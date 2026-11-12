# i_frequency_sweep_export_port — Intention

## Rationale

Un fond ne sert qu'à être relu : soustrait d'une mesure objet, comparé à un autre fond, combiné en profil. Il doit donc quitter la session sous une forme qui se relit sans le logiciel, avec les conditions de son acquisition à côté.

## Responsibility

- `open_export(role, table_height_mm)` : créer le dossier du balayage au démarrage (les paramètres y sont écrits pendant qu'il tourne).
- `export(location, result, samples)` : écrire la réponse par fréquence et les échantillons bruts ; retourner les fichiers écrits (taille, SHA-256).
- `write_acquisition_parameters(location, parameters)` : (ré)écrire les paramètres d'acquisition.

## Design

- Calque `IAcquisitionThroughputExportPort`. Le port possède le format ; il reçoit des DTOs sans format.
- Échec d'entrée/sortie attendu → `OperationResult.fail`, jamais une exception.
