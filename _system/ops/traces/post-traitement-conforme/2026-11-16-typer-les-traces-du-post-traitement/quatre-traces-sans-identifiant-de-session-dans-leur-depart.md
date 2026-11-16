---
type: constat::sh-agent-os
genere_par: "[[tache - typer les traces du post-traitement]]"
---

# Quatre départs de trace sans identifiant de session

Le format attendu est `HH:MM | depart | quoi=... | session=<id complet>`. Une seule des cinq traces le respecte (`2026-11-12-concevoir-l-architecture-par-panneaux`, session `1d02b818-19d3-4491-9d3e-c19319943da8`).

- `2026-11-16-avis-solidai-sur-la-conception` : pas de champ `session` (`heure=reconstituee` à la place).
- `2026-11-16-tranche-1-etapes-1-0-a-1-3`, `…-1-6-et-1-7`, `…-1-8-et-1-9` : `session=sous-agent au-aefi-acquisition`, un type d'agent et non un identifiant.

Les identifiants réels des sous-agents d'origine ne sont écrits nulle part dans le dépôt : je ne les ai pas inventés, et les premières lignes sont restées telles quelles, comme la consigne le demandait pour les sessions inscrites. `generer_note_tache.ts` a écrit les quatre notes sans erreur : l'absence d'identifiant n'a pas d'effet sur le moteur.

À lever par : relire les transcripts de session de ces sous-agents (hors dépôt) si l'identifiant doit figurer.
