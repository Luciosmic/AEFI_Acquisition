---
name: 'SolidAI — Aggregate Domain : Racine, Entités, Value Objects et Events'
alwaysApply: true
description: 'SolidAI — Aggregate Domain : Racine, Entités, Value Objects et Events'
---

# Standard: SolidAI — Aggregate Domain : Racine, Entités, Value Objects et Events

Ce standard définit l'anatomie d'un module domain dans SolidAI. Chaque module domain représente un agrégat : le seul fichier de code à la racine est l'aggregate root, qui porte l'identité et les invar... :
* Créer un sous-dossier repositories/ à la racine du module domain pour y placer les interfaces de repository de l'agrégat — ces interfaces expriment le contrat de persistance du domain sans dépendance infrastructure
* Implémenter l'aggregate root comme dataclass Python portant les invariants métier et les méthodes de mutation — sans import hors domain/ et sans logique d'infrastructure
* Isoler chaque entité de l'agrégat dans domain/X/entities/Y/ avec son propre Trio Atomique (<entity>_intention.md, <entity>.py, _tests/) — une entité a une identité propre mais n'est pas la racine de l'agrégat
* Isoler chaque événement domain de l'agrégat dans domain/X/events/Y/ avec son propre Trio Atomique (<event>_intention.md, <event>.py, _tests/) — un événement est immuable et représente un fait passé dans le domain
* Isoler chaque value object dans domain/X/value_objects/Y/ avec son propre Trio Atomique (<vo>_intention.md, <vo>.py, _tests/) — un value object est immuable, sans identité, défini uniquement par sa valeur
* Placer exactement un seul fichier de code à la racine du module domain — l'aggregate root — avec son <module>_intention.md et son dossier _tests/ ; ne jamais y placer d'entités, value objects ou events

Full standard is available here for further request: [SolidAI — Aggregate Domain : Racine, Entités, Value Objects et Events](../../../.packmind/standards/solidai-aggregate-domain-racine-entites-value-objects-et-events.md)