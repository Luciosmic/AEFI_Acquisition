---
name: 'SolidAI — Aggregate Domain : Racine, Entités, Value Objects et Events'
alwaysApply: true
description: 'Standardiser l’anatomie des modules domain SolidAI en structurant chaque agrégat avec un unique aggregate root Python dataclass à la racine (Trio Atomique <module>_intention.md + implémentation + _tests/), des entités/value objects/events isolés dans entities/, value_objects/ et events/ avec leur propre Trio Atomique, et des interfaces dans repositories/ sans imports hors domain/ ni logique d’infrastructure afin de préserver les invariants, éviter les collisions de noms et améliorer la maintenabilité.'
---

# Standard: SolidAI — Aggregate Domain : Racine, Entités, Value Objects et Events

Standardiser l’anatomie des modules domain SolidAI en structurant chaque agrégat avec un unique aggregate root Python dataclass à la racine (Trio Atomique <module>_intention.md + implémentation + _tests/), des entités/value objects/events isolés dans entities/, value_objects/ et events/ avec leur propre Trio Atomique, et des interfaces dans repositories/ sans imports hors domain/ ni logique d’infrastructure afin de préserver les invariants, éviter les collisions de noms et améliorer la maintenabilité. :
* Créer un sous-dossier repositories/ à la racine du module domain pour y placer les interfaces de repository de l'agrégat — ces interfaces expriment le contrat de persistance du domain sans dépendance infrastructure
* Implémenter l'aggregate root comme dataclass Python portant les invariants métier et les méthodes de mutation — sans import hors domain/ et sans logique d'infrastructure
* Isoler chaque entité de l'agrégat dans domain/X/entities/Y/ avec son propre Trio Atomique (<entity>_intention.md, <entity>.py, _tests/) — une entité a une identité propre mais n'est pas la racine de l'agrégat
* Isoler chaque événement domain de l'agrégat dans domain/X/events/Y/ avec son propre Trio Atomique (<event>_intention.md, <event>.py, _tests/) — un événement est immuable et représente un fait passé dans le domain
* Isoler chaque value object dans domain/X/value_objects/Y/ avec son propre Trio Atomique (<vo>_intention.md, <vo>.py, _tests/) — un value object est immuable, sans identité, défini uniquement par sa valeur
* Placer exactement un seul fichier de code à la racine du module domain — l'aggregate root — avec son <module>_intention.md et son dossier _tests/ ; ne jamais y placer d'entités, value objects ou events

Full standard is available here for further request: [SolidAI — Aggregate Domain : Racine, Entités, Value Objects et Events](../../../.packmind/standards/solidai-aggregate-domain-racine-entites-value-objects-et-events.md)