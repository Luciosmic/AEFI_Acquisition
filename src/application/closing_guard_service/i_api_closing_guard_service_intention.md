---
type: port::solidai-hexagonal
tldr: "Port entrant `i_api_closing_guard_service` : `can_close()` dit si l'application peut se fermer maintenant, et sinon quelles acquisitions exportent encore."
sens: entrant
code: "[[src/application/closing_guard_service/i_api_closing_guard_service.py]]"
---
# i_api_closing_guard_service — Intention

## Rationale

L'interface reçoit les demandes de fermeture (fenêtre, arrêt de la session) et doit décider sans rien savoir des exports.
Un contrat d'entrée stable lui suffit : elle ne dépend pas du service concret.

## Responsibility

- `can_close() -> CloseDecisionDTO` : `allowed` vrai sans export ouvert ; sinon faux, avec les acquisitions ouvertes.

## Design

- Requête sans effet de bord sur les exports ; elle logue sa décision.
