---
name: 'SolidAI — Aggregate Domain : Racine, Entités et Value Objects'
alwaysApply: true
description: 'Standardize each SolidAI domain module as a single-aggregate structure with one dataclass aggregate root at the module root (Trio Atomique: <module>_intention.md + implementation + _tests/), entities in entities/, immutable identityless value objects in value_objects/, and immutable domain events in events/ (each with its own Trio Atomique) to make aggregate boundaries, invariants, and responsibilities immediately navigable and unambiguous.'
---

# Standard: SolidAI — Aggregate Domain : Racine, Entités et Value Objects

Standardize each SolidAI domain module as a single-aggregate structure with one dataclass aggregate root at the module root (Trio Atomique: <module>_intention.md + implementation + _tests/), entities in entities/, immutable identityless value objects in value_objects/, and immutable domain events in events/ (each with its own Trio Atomique) to make aggregate boundaries, invariants, and responsibilities immediately navigable and unambiguous. :
* Implémenter l'aggregate root comme dataclass portant les invariants métier et exposant les méthodes de mutation de l'agrégat — sans logique d'infrastructure ni import hors domain/
* Isoler chaque entité de l'agrégat dans domain/X/entities/ avec son propre Trio Atomique — une entité a une identité propre mais n'est pas la racine de l'agrégat
* Isoler chaque value object dans domain/X/value_objects/ avec son propre Trio Atomique — un value object est immuable, sans identité, défini uniquement par sa valeur
* Isoler les événements domain de l'agrégat dans domain/X/events/Y/ avec leur propre Trio Atomique — un événement domain est immuable, représente un fait passé, et ne dépend que du domain/
* Placer exactement un seul fichier de code à la racine du module domain — l'aggregate root — accompagné de son <module>_intention.md et de son dossier _tests/ ; ne jamais y placer d'entités ni de value objects

Full standard is available here for further request: [SolidAI — Aggregate Domain : Racine, Entités et Value Objects](../../../.packmind/standards/solidai-aggregate-domain-racine-entites-et-value-objects.md)