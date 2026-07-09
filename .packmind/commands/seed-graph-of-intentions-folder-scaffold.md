Crée la graine du dépôt `graph_of_intentions/` (thoughts_interface, promise_model, code_interface) avec la structure minimale et des placeholders pour démarrer la cristallisation.

## When to Use

- Démarrer un nouveau projet SolidAI/Graph of Intentions dans un repo vide
- Réinitialiser un workspace de notes/graph avant une première modélisation
- Standardiser la structure entre plusieurs équipes/projets

## Context Validation Checkpoints

* [ ] Le dossier cible (ex: `graph_of_intentions/`) existe-t-il déjà et doit-il être conservé/merge ?
* [ ] Souhaite-t-on inclure des `.gitkeep` (pour versionner les dossiers vides) ?
* [ ] Le projet utilise-t-il exactement les 3 interfaces (thoughts/promise/code) ou une variante ?

## Recipe Steps

### Step 1: Créer l’arborescence de base

Créer les dossiers décrits dans la graine (thoughts_interface, promise_model, code_interface) et leurs sous-dossiers (concepts/events/functionalities/contexts, promises/scopes/etc.).

```bash
mkdir -p graph_of_intentions/{thoughts_interface/{inbox,concepts/{strategic,tactical},events,functionalities/{commands,policies},contexts},promise_model/{agents,promises/{expose,emit,accept,react},scopes,invariants,cooperations,superagents},code_interface/{domain/{aggregates,entities,value_objects,services,events},application/{use_cases,services},infrastructure/{repositories,adapters}}}
```

### Step 2: Ajouter des placeholders versionnables

Ajouter des fichiers `.gitkeep` (ou équivalents) dans les dossiers vides pour garantir que la structure est bien committée.

```bash
find graph_of_intentions -type d -empty -exec touch {}/.gitkeep \;
```

### Step 3: Valider la cohérence de la taxonomie

Vérifier que la structure reflète la séparation Domain/Application/Infra au niveau des notes et la bijection Promise↔DDD au niveau du pivot (promise_model).
