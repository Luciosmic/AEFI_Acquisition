---
type: constat::sh-agent-os
genere_par: "[[tache - reduire la dette solidai vague 5 suite]]"
doc_type: constat
statut: to_validate
---

# `inertial_probe` et `lidar` : créer une racine d'agrégat, ou rester sans

**Lot sauté** : créer ces deux racines revient à inventer du code Python (une classe `@dataclass` racine, ses invariants) qu'aucun comportement actuel ne demande, et l'intention de `domain/inertial_probe` dit le contraire : « l'agrégat racine viendra avec la détection de stabilité, pas avant ».

Ce que coûte de ne pas le faire : 4 intentions `intention-non-typee` (les 3 événements d'`inertial_probe`, `lidar_distance`), 1 erreur D14 (`inertial_probe` importe le noyau sans pouvoir figurer dans `utilise_par`) et 1 `intention-mal-nommee` (`inertial_probe_intention.md` ne nomme aucun module).

## Deux voies

1. **Racine minimale** : une classe `InertialProbe` (identité de la carte, état connecté ou non) et une classe `Lidar`, chacune avec son test. Ajoute du code et un invariant que le métier n'a pas encore énoncé.
2. **Événements dans le noyau partagé** : déplacer les 3 événements d'`inertial_probe` sous `domain/shared_kernel/events/` (comme les 13 événements de mouvement et d'excitation de ce lot). Aucun code nouveau, D14 se règle, mais le noyau grossit d'un contexte qui n'est pas partagé aujourd'hui.

Recommandation : la voie 2 si la détection de stabilité tarde, la voie 1 le jour où elle arrive.
