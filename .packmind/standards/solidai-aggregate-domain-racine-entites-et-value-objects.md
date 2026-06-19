# SolidAI — Aggregate Domain : Racine, Entités et Value Objects

Ce standard définit l'anatomie d'un module domain dans SolidAI. 

Chaque module domain représente un agrégat : le seul fichier de code à la racine du module est l'aggregate root, qui porte l'identité et les invariants de l'agrégat. 

Les entités dépendantes sont isolées dans un sous-dossier entities/, les value objects dans value\_objects/.&#x20;

Chaque composant (root, entité, value object) respecte le Trio Atomique : <module>\_intention.md + fichier d'implémentation + \_tests/.&#x20;

Cette structure garantit une navigation immédiate : en arrivant dans un module domain, on identifie sans ambiguïté le cœur de l'agrégat et la responsabilité de chaque composant.

## Rules

* Placer exactement un seul fichier de code à la racine du module domain — l'aggregate root — accompagné de son <module>_intention.md et de son dossier _tests/ ; ne jamais y placer d'entités ni de value objects
* Isoler chaque entité de l'agrégat dans domain/X/entities/ avec son propre Trio Atomique — une entité a une identité propre mais n'est pas la racine de l'agrégat
* Isoler chaque value object dans domain/X/value_objects/ avec son propre Trio Atomique — un value object est immuable, sans identité, défini uniquement par sa valeur
* Implémenter l'aggregate root comme dataclass portant les invariants métier et exposant les méthodes de mutation de l'agrégat — sans logique d'infrastructure ni import hors domain/
* Isoler les événements domain de l'agrégat dans domain/X/events/Y/ avec leur propre Trio Atomique — un événement domain est immuable, représente un fait passé, et ne dépend que du domain/
