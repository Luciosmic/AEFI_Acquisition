---
type: port::solidai-hexagonal
tldr: "Port sortant `i_system_session_guard` : `hold(reason)` retient l'arrêt de la session et la veille du système, `release()` les rend."
sens: sortant
code: "[[src/application/closing_guard_service/ports/i_system_session_guard.py]]"
---
# i_system_session_guard — Intention

## Rationale

Un arrêt ou un redémarrage du système pendant un export perd la mesure aussi sûrement qu'un opérateur qui ferme la fenêtre.
Ce qu'on peut demander au système dépend du système : Windows affiche une raison de blocage et accepte une demande anti-veille, d'autres systèmes ont leurs propres mécanismes.
Le service de garde doit rester le même partout.

## Responsibility

- `hold(reason)` : retenir l'arrêt de la session et la veille, avec une raison lisible par l'opérateur. Une raison vide est refusée (`ValueError`) : le système n'aurait rien à montrer.
- `release()` : rendre l'arrêt et la veille. Sans `hold` préalable, ne fait rien.

## Design

- Adaptateurs : `null_system_session_guard` (systèmes non pris en charge, et Windows avant son adaptateur), son Fake ; plus tard l'adaptateur Windows.
- Suite de contrat : `_tests/system_session_guard_contract_test.py` du service, jouée par chaque implémentation.
- Appelé depuis le fil qui publie l'ouverture ou la fermeture d'un export : une implémentation doit le tolérer.
