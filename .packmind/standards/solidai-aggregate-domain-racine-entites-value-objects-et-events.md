# SolidAI — Aggregate Domain : Racine, Entités, Value Objects et Events

Ce standard définit l'anatomie d'un module domain dans SolidAI. Chaque module domain représente un agrégat : le seul fichier de code à la racine est l'aggregate root, qui porte l'identité et les invariants de l'agrégat. Les entités dépendantes sont isolées dans entities/, les value objects dans value_objects/, les événements domain dans events/. Chaque composant respecte le Trio Atomique : &lt;module&gt;_intention.md + fichier d'implémentation + _tests/. Le fichier d'intention est toujours préfixé par le nom du module pour éviter les collisions de noms dans les éditeurs et la navigation agents IA.

## Rules

* Placer exactement un seul fichier de code à la racine du module domain — l'aggregate root — avec son <module>_intention.md et son dossier _tests/ ; ne jamais y placer d'entités, value objects ou events
* Isoler chaque entité de l'agrégat dans domain/X/entities/Y/ avec son propre Trio Atomique (<entity>_intention.md, <entity>.py, _tests/) — une entité a une identité propre mais n'est pas la racine de l'agrégat
* Isoler chaque value object dans domain/X/value_objects/Y/ avec son propre Trio Atomique (<vo>_intention.md, <vo>.py, _tests/) — un value object est immuable, sans identité, défini uniquement par sa valeur
* Isoler chaque événement domain de l'agrégat dans domain/X/events/Y/ avec son propre Trio Atomique (<event>_intention.md, <event>.py, _tests/) — un événement est immuable et représente un fait passé dans le domain
* Implémenter l'aggregate root comme dataclass Python portant les invariants métier et les méthodes de mutation — sans import hors domain/ et sans logique d'infrastructure
* Créer un sous-dossier repositories/ à la racine du module domain pour y placer les interfaces de repository de l'agrégat — ces interfaces expriment le contrat de persistance du domain sans dépendance infrastructure
