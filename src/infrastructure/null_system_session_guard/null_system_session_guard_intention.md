---
type: adaptateur::solidai-hexagonal
tldr: "Adaptateur `null_system_session_guard` : la garde de session des systèmes non pris en charge ; ne retient rien et le logue."
code: ["[[src/infrastructure/null_system_session_guard/null_system_session_guard.py]]"]
cause_de_changement: outil
implements: ["[[src/application/closing_guard_service/ports/i_system_session_guard_intention]]"]
---
# null_system_session_guard — Intention

## Rationale

Le service de garde demande au système de retenir son arrêt, mais seul Windows a son adaptateur prévu, et il n'est pas encore écrit.
Sans adaptateur pour les autres cas, l'application ne démarrerait pas ailleurs, ou le service devrait tester le système lui-même.
Le refus de fermer la fenêtre et le refus de l'arrêt de session passent par Qt et marchent déjà sans lui : seuls la raison affichée par le système et l'anti-veille manquent.

## Responsibility

- `hold(reason)` : ne retient rien, logue que la garde de session n'est pas prise en charge sur ce système, avec la raison. Refuse une raison vide, comme tout adaptateur du port.
- `release()` : ne rend rien, logue le relâchement s'il y avait eu un `hold`, et ne dit rien sinon.

## Design

- Choisi au point de composition pour un système autre que Windows, et pour Windows tant que son adaptateur n'existe pas.
- Joue la suite de contrat du port.
