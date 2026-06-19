# SolidAI — Graph of Intentions (Promise↔DDD) Modeling

Standard de modélisation pour transformer une intention utilisateur en graphe de notes traçables (thoughts_interface), la formaliser via Promise Theory (promise_model) puis la projeter en structures DDD implémentables (code_interface), en garantissant cohérence sémantique, invariants, et extraction de fonctionnalités atomiques (N-atomicité).

## Rules

* Maintenir la séparation en trois espaces `thoughts_interface/`, `promise_model/`, `code_interface/` et retarder la documentation d’infrastructure jusqu’à extraction d’une fonctionnalité atomique validée.
* Tracer la provenance de chaque note (S_user, S_retroing, S_doc) et conserver l’utilisateur comme terme source dominant (toute FA doit avoir une source S_user).
* Nommer et distinguer explicitement Commands (impératif) et Domain Events (passé) et ne pas les mélanger.
* Appliquer la bijection Promise Theory ↔ DDD_Core (Agent↔Aggregate Root, +emit↔Domain Event, +expose/-accept↔Commands, Scope↔Bounded Context, Cooperation↔Use Case, Body↔Invariant, Assessment↔Tests).
* Définir une fonctionnalité atomique (FA) par la cohésion irréductible de l’intention et son ordre d’atomicité N (nombre d’Aggregate Roots impliqués), plutôt que par une frontière technique.
* Exiger une orchestration applicative explicite quand N>1 (Process Manager / Saga / Use Case multi-aggregates) et vérifier les invariants de chaque aggregate + invariants de liaison en fin d’opération.
* Préserver l’indépendance d’infrastructure au niveau domaine (pas de dépendances infra dans Domain Model; entrées/sorties exprimées en objets du domaine).
* Tisser des liens minimaux mais suffisants: intention→(events)→(aggregate)→(strategies/use cases) et rejeter une FA candidate si la cohérence de bounded context ou l’atomicité échoue.
