# i_operator_repository — Intention

## Rationale

Le registre des opérateurs doit survivre aux redémarrages. Sans contrat de
persistance côté domaine, l'aggregate ou le service connaîtraient le fichier
JSON ; et un registre illisible risquerait d'être traité comme « aucun
opérateur », puis écrasé au premier ajout — tous les opérateurs perdus.

## Responsibility

- `find_all()` : tous les opérateurs enregistrés, ou un échec lisible.
- `add(operator)` : persister un nouvel opérateur, ou un échec lisible.

## Design

- ABC pure, dans le module domaine (`domain/operator_registry/repositories/`).
- `OperationResult` pour les échecs attendus (registre illisible, non
  écrivable) : jamais d'exception, jamais une liste vide à la place d'un échec.
- Implémentations : `infrastructure/persistence/operator_registry/real_operator_repository.py`
  et son Fake co-localisé.
