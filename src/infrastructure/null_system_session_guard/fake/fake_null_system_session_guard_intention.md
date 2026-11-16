---
type: doublure-de-test::solidai-hexagonal
tldr: "Doublure `fake_null_system_session_guard` : garde de session en mémoire qui retient chaque `hold` et `release`, pour les tests et le mode simulation."
code: ["[[src/infrastructure/null_system_session_guard/fake/fake_null_system_session_guard.py]]"]
cause_de_changement: outil
implements: ["[[src/application/closing_guard_service/ports/i_system_session_guard_intention]]"]
double_de: "[[src/infrastructure/null_system_session_guard/null_system_session_guard_intention]]"
---
# fake_null_system_session_guard — Intention

## Rationale

Le test du service de garde doit vérifier qu'il retient le système au premier export ouvert et le relâche au dernier fermé.
L'adaptateur neutre ne garde aucune trace, et l'adaptateur Windows toucherait la vraie session : ni l'un ni l'autre ne se lit dans un test.

## Responsibility

- Tenir la promesse du port : refuser une raison vide, retenir, relâcher, relâcher sans effet sans `hold`.
- Retenir les raisons reçues (`holds`), le nombre de relâchements effectifs (`releases`) et l'état courant (`is_holding`).
- Loguer chaque `hold` et `release`, pour qu'on les voie en mode simulation.

## Design

- Vérification d'état, pas d'interactions.
- Instantané : le réel est un appel système court, aucune régulation ne dépend de sa latence.
- Sûr entre fils : un verrou protège l'état.
