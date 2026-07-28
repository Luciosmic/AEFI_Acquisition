---
description: 'Document an atomic functionality fa from an intention'
---

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
* [ ] Quelle est l'union d'erreurs (refus métier) du Use Case, exprimée en ubiquitous language ?
* [ ] Chaque invariant a-t-il un Domain error nommé qui exprime son refus (nommé par la promesse refusée, pas par le mécanisme d'exception) ?

## Recipe Steps

### Step 1: Event-storming interactif (S_user)

Poser des questions jusqu’à obtenir: une Command (impératif), un ou plusieurs Domain Events (passé), et un critère de succès observable. Créer les notes dans `thoughts_interface/` et tagguer (#domain/#application/#infra) + ajouter une section "Sources" avec la trace utilisateur.

### Step 2: Identifier les aggregates & invariants

Relier chaque event à un Aggregate Root candidate; expliciter invariants (règles "doit/jamais/toujours"). Déterminer l’ordre N = nombre d’Aggregate Roots réellement irréductibles.

### Step 2.5: Enumerate refused promises (Domain errors)

Pour chaque invariant identifié à l'étape 2, nommer le Domain error qui exprime son refus en ubiquitous language (ex : `ScanAlreadyRunning`, pas `IllegalStateException`). Consigner ces refus dans une section "Refusals" de la note FA (`thoughts_interface/`). Un invariant sans Domain error nommé n'est pas testable ni orchestrable en aval.

### Step 3: Tisser les liens et vérifier la cohérence de contexte

Relier event→aggregate→stratégies/use cases. Rejeter la FA candidate si les éléments ne partagent pas un bounded context cohérent (ubiquitous language).

### Step 4: Valider l’atomicité (irréductibilité)

Tester mentalement (ou via checklist) si la fonctionnalité peut être scindée en deux fonctionnalités complètes sans violer un invariant ou laisser un état incohérent. Si N>1, exiger orchestration applicative explicite.

### Step 4.5: Déclarer l'union d'erreurs du Use Case

Composer l'union d'erreurs du Use Case en agrégeant : (a) les Domain refusals collectés à l'étape 2.5, (b) les refusals de niveau applicatif (préconditions cross-aggregate, autorisations métier). Les erreurs Infrastructure n'apparaissent **jamais** dans l'union du Use Case — elles sont traduites au boundary du service. Consigner l'union dans la note FA à côté de la Command.

### Step 5: Projeter vers Promise Model

Mapper: Aggregate Root→Agent; Command→(+expose/-accept); Event→(+emit) et (react) côté consommateurs; Invariants→Bodies; Use Case multi-aggregates→Cooperation/Superagent. Étendre le mapping : Domain refusal → `-reject` (assessment d'un body cassé) ; l'union d'erreurs du Use Case → catalogue de promesses refusées exposé par le Superagent.

### Step 6: Projeter vers code_interface (DDD)

Créer le squelette DDD: `domain/aggregates`, `domain/events`, `application/use_cases` (et éventuellement `application/services` si superagent), en gardant le domaine indépendant de l’infrastructure. La projection produit **aussi** un fichier `<use_case>_errors.py` co-localisé avec le use case, déclarant l'union d'erreurs identifiée à l'étape 4.5.
