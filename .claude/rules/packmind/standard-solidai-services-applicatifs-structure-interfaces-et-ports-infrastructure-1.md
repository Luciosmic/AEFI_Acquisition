---
name: 'SolidAI — Services Applicatifs : Structure, Interfaces et Ports Infrastructure'
alwaysApply: true
description: 'Définit la structure obligatoire d''un service applicatif : interface API inbound (i_api_), ports outbound dans application/X_service/ports/ (i_), DTOs, et co-localisation en trio atomique.'
---

# Standard: SolidAI — Services Applicatifs : Structure, Interfaces et Ports Infrastructure

Définit la structure obligatoire d'un service applicatif : interface API inbound (i_api_), ports outbound dans application/X_service/ports/ (i_), DTOs, et co-localisation en trio atomique. :
* Créer les DTOs Request/Response systématiquement dans dtos/, même vides, avec @dataclass(frozen=True) — jamais de primitives éclatées en signature de méthode
* Déclarer les ports outbound vers l'Infrastructure dans application/X_service/ports/ — ces ports expriment un besoin technique de l'Application, pas un concept du Domain
* Distinguer explicitement le sens des interfaces : i_api_ est inbound (Adapters → Application), i_ dans ports/ est outbound (Application → Infrastructure)
* Préfixer l'interface inbound du service avec i_api_ pour la distinguer sans ambiguïté des ports outbound et des interfaces Domain
* Structurer chaque service applicatif avec le trio atomique obligatoire : X_service_intention.md, i_api_X_service.py, dtos/, X_service.py, et _tests/ — sans exception

Full standard is available here for further request: [SolidAI — Services Applicatifs : Structure, Interfaces et Ports Infrastructure](../../../.packmind/standards/solidai-services-applicatifs-structure-interfaces-et-ports-infrastructure-1.md)