---
type: adaptateur::solidai-hexagonal
tldr: "Lire l'identifiant de l'activité et l'empreinte du CSV dans le fichier des paramètres d'acquisition rangé à côté de ce CSV."
code: ["[[external_modules/aefi_post_processor_module/infrastructure/acquisition_provenance_reader/acquisition_provenance_reader.py]]"]
cause_de_changement: outil
implements: ["[[external_modules/aefi_post_processor_module/application/post_processing_service/post_processing_service_intention^^i-acquisition-provenance-reader]]"]
---
# acquisition_provenance_reader — Intention

## Rationale

L'acquisition n'exporte plus que le CSV. Le fichier d'étapes que le traitement crée doit dire de quelle activité viennent ses points et si le CSV relu est encore celui que l'acquisition a haché à la fermeture, sans quoi l'empreinte de `data.files` ne prouve plus rien sur ce qu'on a traité. Le fichier des paramètres est le contrat entre les deux logiciels : l'activité est dans `provenance.activity.id`, l'empreinte dans l'entrée de `data.files` qui porte le nom du CSV.

## Responsibility

- Implémenter `IAcquisitionProvenanceReader` : trouver le fichier des paramètres par le nom du CSV, lire `provenance.activity.id` et le `sha256` de l'entrée de `data.files` nommée comme le CSV, rendre les deux.
- Rendre `None`, en le journalisant, pour un CSV que l'acquisition n'a pas nommé, un fichier absent ou illisible ; rendre l'un des deux faits à `None` quand la description ne le dit pas.

## Design

- Une classe, `json` et `pathlib`, la même suite de contrat que son Fake. Le chemin du fichier des paramètres vient de `parameters_path_of`, comme pour la grille prévue.
- Ne lit que ces deux faits : le reste du fichier passe par le catalogue (`export_folder_repository/acl`).
