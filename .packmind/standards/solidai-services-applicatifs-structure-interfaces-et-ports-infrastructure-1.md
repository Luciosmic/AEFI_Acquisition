# SolidAI — Services Applicatifs : Structure, Interfaces et Ports Infrastructure

Ce standard définit l'anatomie complète d'un service applicatif dans SolidAI. Un service applicatif orchestre la logique sans porter de logique métier : il reçoit des commandes via une interface API inbound (i_api_X_service.py), déclare ses besoins vers l'infrastructure via des ports outbound (interfaces i_ dans application/X_service/ports/), et retourne des DTOs immuables. Les ports outbound appartiennent à la couche Application, pas au Domain : c'est l'Application qui exprime le besoin technique (envoyer un email, publier un message), le Domain n'a pas cette connaissance. La séparation inbound/outbound garantit la navigation déterministe des agents IA et l'isolation des couches conformément à l'architecture hexagonale DDD.

## Rules

* Structurer chaque service applicatif avec le trio atomique obligatoire : X_service_intention.md, i_api_X_service.py, dtos/, X_service.py, et _tests/ — sans exception
* Préfixer l'interface inbound du service avec i_api_ pour la distinguer sans ambiguïté des ports outbound et des interfaces Domain
* Déclarer les ports outbound vers l'Infrastructure dans application/X_service/ports/ — ces ports expriment un besoin technique de l'Application, pas un concept du Domain
* Distinguer explicitement le sens des interfaces : i_api_ est inbound (Adapters → Application), i_ dans ports/ est outbound (Application → Infrastructure)
* Créer les DTOs Request/Response systématiquement dans dtos/, même vides, avec @dataclass(frozen=True) — jamais de primitives éclatées en signature de méthode
