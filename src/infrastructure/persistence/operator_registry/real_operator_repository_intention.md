# real_operator_repository — Intention

## Rationale

Le registre des opérateurs doit survivre aux redémarrages, sur le poste
d'acquisition, à côté des autres registres (`.aefi_acquisition/`). Le dépôt
de référence du projet traite un fichier illisible comme un registre vide :
pour les opérateurs, l'ajout suivant réécrirait le fichier et effacerait
tous les noms — exactement la perte que la FA veut éviter.

## Responsibility

- Implémenter `IOperatorRepository` sur
  `.aefi_acquisition/operators/operators.json` :
  `{"operators": [{"operator_id", "name", "registered_at"}]}`.
- Fichier absent = registre vide (premier lancement) ; fichier illisible =
  **échec**, jamais une liste vide ; `add` refuse d'écrire s'il n'a pas pu
  relire le registre.

## Design

- Écriture atomique (fichier temporaire puis remplacement) : jamais un
  registre à moitié écrit.
- `registered_at` en ISO 8601 avec fuseau.
- Toute exception de fichier / JSON est attrapée ici et rendue en
  `OperationResult.fail` lisible.
