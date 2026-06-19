Guide pas-à-pas pour extraire une fonctionnalité atomique (mono/di/N-atomique) depuis une intention utilisateur, tracer ses sources, tisser le graphe, puis la projeter en Promise Model et en DDD (code_interface).

## When to Use

- Transformer une demande floue en intention implémentable (use case + domain events + aggregates)
- Valider qu’une fonctionnalité est irréductible (N-atomicité) avant d’implémenter
- Industrialiser la traçabilité (S_user/S_retroing/S_doc) lors de rétro-ingénierie + RAG

## Context Validation Checkpoints

* [ ] Quelle est l’intention utilisateur exacte (phrase) et quel est le succès observable ?
* [ ] Quels Domain Events (passé) et Commands (impératif) candidats émergent ?
* [ ] Quels Aggregate Roots sont impliqués (N) et quels invariants doivent être préservés ?
* [ ] Y a-t-il un bounded context explicite ou à découvrir ?
* [ ] Si N>1, quel mécanisme d’orchestration (process manager/saga/use case multi-aggregates) est accepté ?

## Recipe Steps

### Step 1: Event-storming interactif (S_user)

Poser des questions jusqu’à obtenir: une Command (impératif), un ou plusieurs Domain Events (passé), et un critère de succès observable. Créer les notes dans `thoughts_interface/` et tagguer (#domain/#application/#infra) + ajouter une section "Sources" avec la trace utilisateur.

### Step 2: Identifier les aggregates & invariants

Relier chaque event à un Aggregate Root candidate; expliciter invariants (règles "doit/jamais/toujours"). Déterminer l’ordre N = nombre d’Aggregate Roots réellement irréductibles.

### Step 3: Tisser les liens et vérifier la cohérence de contexte

Relier event→aggregate→stratégies/use cases. Rejeter la FA candidate si les éléments ne partagent pas un bounded context cohérent (ubiquitous language).

### Step 4: Valider l’atomicité (irréductibilité)

Tester mentalement (ou via checklist) si la fonctionnalité peut être scindée en deux fonctionnalités complètes sans violer un invariant ou laisser un état incohérent. Si N>1, exiger orchestration applicative explicite.

### Step 5: Projeter vers Promise Model

Mapper: Aggregate Root→Agent; Command→(+expose/-accept); Event→(+emit) et (react) côté consommateurs; Invariants→Bodies; Use Case multi-aggregates→Cooperation/Superagent.

### Step 6: Projeter vers code_interface (DDD)

Créer le squelette DDD: `domain/aggregates`, `domain/events`, `application/use_cases` (et éventuellement `application/services` si superagent), en gardant le domaine indépendant de l’infrastructure.
