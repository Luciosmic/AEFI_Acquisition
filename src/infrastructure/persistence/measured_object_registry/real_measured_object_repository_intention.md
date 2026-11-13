---
type: adaptateur::solidai-hexagonal
tldr: "Implémenter IMeasuredObjectRepository sur .aefi_acquisition/measured_objects/measured_objects.json : {\"measured_objects\": [{\"measured_object_id\", \"name\",…"
code: ["[[src/infrastructure/persistence/measured_object_registry/real_measured_object_repository.py]]"]
cause_de_changement: outil
implements: ["[[src/domain/measured_object_registry/measured_object_registry_intention^^i-measured-object-repository]]"]
---
# real_measured_object_repository — Intention

## Rationale

Le registre des objets mesurés doit survivre aux redémarrages, sur le poste
d'acquisition, à côté des autres registres (`.aefi_acquisition/`). Le dépôt
de référence du projet traite un fichier illisible comme un registre vide :
pour les objets mesurés, l'ajout suivant réécrirait le fichier et effacerait
tous les noms — exactement la perte que le registre doit éviter.

## Responsibility

- Implémenter `IMeasuredObjectRepository` sur
  `.aefi_acquisition/measured_objects/measured_objects.json` :
  `{"measured_objects": [{"measured_object_id", "name", "registered_at"}]}`.
- Fichier absent = registre vide (premier lancement) ; fichier illisible =
  **échec**, jamais une liste vide ; `add` et `save_all` refusent d'écrire
  s'ils n'ont pas pu relire le registre.
- `save_all` réécrit tout le registre (renommage, suppression) ; l'objet
  supprimé n'y reste pas, son retrait est gardé par l'événement
  `MeasuredObjectDeleted` du journal.

## Design

- Écriture atomique (fichier temporaire puis remplacement) : jamais un
  registre à moitié écrit.
- `registered_at` en ISO 8601 avec fuseau.
- Toute exception de fichier / JSON est attrapée ici et rendue en
  `OperationResult.fail` lisible.
