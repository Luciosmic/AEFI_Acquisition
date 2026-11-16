---
type: service-applicatif::solidai-hexagonal
tldr: "Service applicatif `closing_guard_service` : suivre les exports d'acquisition ouverts, dire si l'application peut se fermer, et retenir l'arrêt de la session système tant qu'un export est ouvert."
code: ["[[src/application/closing_guard_service/closing_guard_service.py]]"]
cause_de_changement: orchestration
---
# closing_guard_service — Intention

## Rationale

Une acquisition réelle dure des heures et écrit son export au fil de l'eau.
Si l'application se ferme pendant ce temps, par l'opérateur ou par un arrêt du système, la mesure est perdue ou tronquée.
Chaque service d'export sait seulement le sien : sans un seul endroit qui les suit tous, la fenêtre devrait interroger chaque service, et oublierait le prochain qui exportera.
Une simple lecture affichée sans export ne doit rien bloquer : l'opérateur ferme alors librement.

## Responsibility

- Suivre les exports ouverts à partir des événements `AcquisitionExportOpened` et `AcquisitionExportClosed`, d'où qu'ils viennent.
- Répondre à « l'application peut-elle se fermer maintenant ? » (`can_close`) : oui sans export ouvert ; sinon non, avec chaque acquisition ouverte (sorte, identifiant, objet mesuré).
- Retenir l'arrêt de la session système (`hold`) à l'ouverture du premier export, et le relâcher (`release`) à la fermeture du dernier : un seul `hold` pour plusieurs exports ouverts ensemble.
- Ignorer, en le loguant, une ouverture déjà suivie et une fermeture inconnue : ni second `hold`, ni `release` à tort.
- Loguer chaque décision : fermeture refusée avec les acquisitions ouvertes, fermeture acceptée.

## Design

- N'appelle aucun service d'export : ce sont eux qui publient l'ouverture et la fermeture, et la garde s'abonne au bus (`IDomainEventBus`).
- Un export ouvert se reconnaît par la paire (sorte, identifiant).
- Les événements arrivent de plusieurs fils (boucle du scan, tâche du balayage) et `can_close` du fil de l'interface : l'état est protégé par un verrou.
- Le port sortant `ISystemSessionGuard` cache le système d'exploitation : le service ne sait pas s'il tourne sous Windows.
- La raison donnée au système (`HOLD_REASON`) est celle que Windows affichera à l'étape de l'adaptateur Windows.
- `can_close` est une requête sans argument : pas de DTO de requête (H8).

## Ports

- [[src/application/closing_guard_service/i_api_closing_guard_service_intention]] : port entrant, `can_close()`.
- [[src/application/closing_guard_service/ports/i_system_session_guard_intention]] : port sortant, `hold(reason)` et `release()`.
