# i_measured_object_repository — Intention

## Rationale

Le registre des objets mesurés doit survivre aux redémarrages. Sans contrat de
persistance côté domaine, l'aggregate ou le service connaîtraient le fichier
JSON ; et un registre illisible risquerait d'être traité comme « aucun
objet mesuré », puis écrasé au premier ajout — tous les objets mesurés perdus.

## Responsibility

- `find_all()` : tous les objets mesurés enregistrés, ou un échec lisible.
- `add(measured_object)` : persister un nouvel objet mesuré, ou un échec lisible.

## Design

- ABC pure, dans le module domaine (`domain/measured_object_registry/repositories/`).
- `OperationResult` pour les échecs attendus (registre illisible, non
  écrivable) : jamais d'exception, jamais une liste vide à la place d'un échec.
- Implémentations : `infrastructure/persistence/measured_object_registry/real_measured_object_repository.py`
  et son Fake co-localisé.
