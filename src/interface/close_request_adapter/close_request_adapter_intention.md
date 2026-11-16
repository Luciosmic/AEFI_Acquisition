---
type: adaptateur-entrant::solidai-hexagonal
tldr: "Adaptateur entrant `close_request_adapter` : reçoit la fermeture de la fenêtre principale et la demande d'arrêt de session venue de Qt, demande à la garde si l'application peut se fermer, puis accepte ou refuse."
code: ["[[src/interface/close_request_adapter/close_request_adapter.py]]"]
cause_de_changement: outil
appelle: ["[[src/application/closing_guard_service/i_api_closing_guard_service_intention]]"]
---
# close_request_adapter — Intention

## Rationale

L'application se ferme par deux chemins : l'opérateur ferme la fenêtre principale (croix, Alt+F4, barre des tâches), ou le système demande la fin de la session (arrêt, redémarrage, déconnexion), ce que Qt transmet de la même façon sous Windows, Linux et macOS.
Si l'un des deux chemins ne passe pas par la garde, une acquisition en cours peut être coupée pendant qu'elle écrit son export.

## Responsibility

- `on_window_close()` : demander à la garde (`can_close`) ; refusé, faire afficher le message par le présentateur et rendre faux ; accepté, rendre vrai. La fenêtre applique la réponse.
- `on_session_end_request(manager)` : demander à la garde ; refusé, annuler la fin de session (`manager.cancel()`) après avoir demandé au système le droit d'interagir (`allowsInteraction`). Pas de boîte de message : le système affiche son propre écran.
- Loguer chaque demande reçue et ce qui en a été fait.

## Design

- Aucune règle : la décision vient de la garde, le texte du présentateur.
- Ne connaît ni les exports ni le système d'exploitation.
- Le gestionnaire de session est reçu tel quel (`QSessionManager` en vrai, un double dans les tests) : seules `allowsInteraction()` et `cancel()` servent.
