---
name: 'SolidAI — Graph of Intentions (Promise↔DDD) Modeling'
alwaysApply: true
description: 'Appliquer une taxonomie stable et traçable (sources, tags, mappings) pour faire émerger des fonctionnalités atomiques et guider leur projection en DDD.'
---

# Standard: SolidAI — Graph of Intentions (Promise↔DDD) Modeling

Appliquer une taxonomie stable et traçable (sources, tags, mappings) pour faire émerger des fonctionnalités atomiques et guider leur projection en DDD. :
* Appliquer la bijection Promise Theory ↔ DDD_Core (Agent↔Aggregate Root, +emit↔Domain Event, +expose/-accept↔Commands, Scope↔Bounded Context, Cooperation↔Use Case, Body↔Invariant, Assessment↔Tests).
* Définir une fonctionnalité atomique (FA) par la cohésion irréductible de l’intention et son ordre d’atomicité N (nombre d’Aggregate Roots impliqués), plutôt que par une frontière technique.
* Exiger une orchestration applicative explicite quand N>1 (Process Manager / Saga / Use Case multi-aggregates) et vérifier les invariants de chaque aggregate + invariants de liaison en fin d’opération.
* Maintenir la séparation en trois espaces `thoughts_interface/`, `promise_model/`, `code_interface/` et retarder la documentation d’infrastructure jusqu’à extraction d’une fonctionnalité atomique validée.
* Nommer et distinguer explicitement Commands (impératif) et Domain Events (passé) et ne pas les mélanger.
* Préserver l’indépendance d’infrastructure au niveau domaine (pas de dépendances infra dans Domain Model; entrées/sorties exprimées en objets du domaine).
* Tisser des liens minimaux mais suffisants: intention→(events)→(aggregate)→(strategies/use cases) et rejeter une FA candidate si la cohérence de bounded context ou l’atomicité échoue.
* Tracer la provenance de chaque note (S_user, S_retroing, S_doc) et conserver l’utilisateur comme terme source dominant (toute FA doit avoir une source S_user).

Full standard is available here for further request: [SolidAI — Graph of Intentions (Promise↔DDD) Modeling](../../../.packmind/standards/solidai-graph-of-intentions-promiseddd-modeling.md)