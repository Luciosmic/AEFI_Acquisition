---
description: 'Seed graph of intentions folder scaffold'
---

Crée la graine du dépôt `graph_of_intentions/` (thoughts_interface, promise_model, code_interface) avec la structure minimale et des placeholders pour démarrer la cristallisation.

## When to Use

- Démarrer un nouveau projet SolidAI/Graph of Intentions dans un repo vide
- Réinitialiser un workspace de notes/graph avant une première modélisation
- Standardiser la structure entre plusieurs équipes/projets

## Context Validation Checkpoints

* [ ] Le dossier cible (ex: `graph_of_intentions/`) existe-t-il déjà et doit-il être conservé/merge ?
* [ ] Souhaite-t-on inclure des `.gitkeep` (pour versionner les dossiers vides) ?
* [ ] Le projet utilise-t-il exactement les 3 interfaces (thoughts/promise/code) ou une variante ?
* [ ] Le shared kernel expose-t-il déjà `OperationResult[T, E]` / `Result[T, E]` ?
* [ ] Les emplacements réservés aux unions d'erreurs (`application/<service>/`, `infrastructure/<adapter>/errors/`) sont-ils présents dans le scaffold ?

## Recipe Steps

### Step 1: Créer l’arborescence de base

Créer les dossiers décrits dans la graine (thoughts_interface, promise_model, code_interface) et leurs sous-dossiers. L'arbre inclut explicitement `code_interface/domain/shared_kernel/` (slot pour `OperationResult[T, E]`) et `code_interface/infrastructure/adapters/errors/` (slot pour les unions d'erreurs adapter-scoped).

```bash
mkdir -p graph_of_intentions/{thoughts_interface/{inbox,concepts/{strategic,tactical},events,functionalities/{commands,policies},contexts},promise_model/{agents,promises/{expose,emit,accept,react},scopes,invariants,cooperations,superagents},code_interface/{domain/{aggregates,entities,value_objects,services,events,shared_kernel},application/{use_cases,services},infrastructure/{repositories,adapters/errors}}}
```

### Step 1.5: Seed the shared kernel for `OperationResult`

Créer `code_interface/domain/shared_kernel/operation_result_intention.md` déclarant `OperationResult[T, E]` / `Result[T, E]` comme la primitive sanctionnée de retour d'échec attendu, partagée par toutes les couches. Si un shared kernel externe fournit déjà cette primitive, vérifier la présence et référencer plutôt que dupliquer.

### Step 1.6: Réserver les emplacements des unions d'erreurs

Documenter la convention pour les futures unions d'erreurs :
- `code_interface/application/<service>/<service>_errors.py` — Use Case error union (créée par `/create-application-service`).
- `code_interface/infrastructure/adapters/errors/<adapter>_errors.py` — union d'erreurs technique de l'adapter (créée par `/create-port-interface`).

Placer un `.gitkeep` dans `infrastructure/adapters/errors/` et documenter les conventions dans un `README` ou `intention.md` à la racine de `application/` pour que les commands en aval trouvent les emplacements.

### Step 2: Ajouter des placeholders versionnables

Ajouter des fichiers `.gitkeep` (ou équivalents) dans les dossiers vides pour garantir que la structure est bien committée.

```bash
find graph_of_intentions -type d -empty -exec touch {}/.gitkeep \;
```

### Step 3: Valider la cohérence de la taxonomie

Vérifier que la structure reflète la séparation Domain/Application/Infra au niveau des notes et la bijection Promise↔DDD au niveau du pivot (promise_model). Confirmer aussi que le shared kernel expose `OperationResult` et que les emplacements pour les unions d'erreurs (application/`<service>`/, infrastructure/adapters/errors/) sont bien présents — sans quoi les commands `/create-application-service` et `/create-port-interface` ne pourront pas honorer la taxonomie sans inventer d'emplacement.
