---
type: atome::solidai-atome
tldr: "Présentateur `closing_guard_presenter` : traduit une fermeture refusée en message à l'opérateur, qui nomme chaque acquisition en cours et dit de l'arrêter d'abord."
code: ["[[src/interface/presenters/closing_guard_presenter.py]]"]
cause_de_changement: outil
---
# closing_guard_presenter — Intention

## Rationale

Quand la fermeture est refusée, l'opérateur doit comprendre pourquoi et quoi faire, sans connaître les noms internes des sortes d'acquisition (`step_scan`, `frequency_sweep`).
Sans présentateur, la fenêtre principale formaterait elle-même la décision et importerait les DTO de l'application.

## Responsibility

- `present_close_refused(decision)` : émettre `close_refused(titre, texte)`, le texte nommant chaque acquisition ouverte (sorte en clair, objet mesuré s'il y en a un) puis demandant de l'arrêter avant de fermer.
- Une sorte inconnue s'affiche telle quelle plutôt que de disparaître.

## Design

- `QObject`, un signal Qt ; la vue (`Dashboard.show_close_refused`) affiche la boîte de message.
- Reçoit le DTO de la décision, n'importe pas le domaine.
- Ne demande rien au service : l'adaptateur de l'action de l'opérateur l'appelle avec la décision. C'est pourquoi il est typé `atome` et non `presenter`, dont le type exige un port entrant appelé.
