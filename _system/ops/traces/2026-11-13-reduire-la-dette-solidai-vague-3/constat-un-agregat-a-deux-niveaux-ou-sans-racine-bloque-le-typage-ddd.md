---
type: constat::sh-agent-os
genere_par: "[[tache - reduire la dette solidai vague 3]]"
doc_type: constat
date: 2026-11-13
---

# Typer les événements et dépôts de `test_bench/calibration` fait apparaître des erreurs de place

**À discuter.** Deux essais ont été retirés du lot avant commit, car ils faisaient monter l'erreur sans rien régler.

## Ce qui a été essayé

| Essai | Verify | Erreurs nouvelles |
| --- | --- | --- |
| 8 événements de `domain/test_bench/calibration/events/` typés `evenement-de-domaine` avec `part_of` vers la racine `calibration` | −8 `intention-non-typee` | +8 `solidai-evenement-mal-place` : D4 veut `domain/<agrégat>/events/<nom>/`, l'agrégat à deux niveaux (`test_bench/calibration`) n'y entre pas |
| 5 dépôts de calibration (port, réel, Fake) typés, enregistrements `repositories:` dans la racine `calibration` | −10 `intention-non-typee`, −5 `port-sortant-sans-fake` | +5 `solidai-repository-mal-place` : D7 veut `domain/<agrégat>/repositories/`, même cause |

La racine `calibration` est typée (famille 1, commit `d17e8be`) : D1 et D6 la passent.
Ses 37 intentions enfants (6 entités, 12 objets-valeurs, 8 événements, 5 dépôts, 4 services, 2 erreurs) restent à typer : D2 et D3 fixent la place des entités et des objets-valeurs comme D4 celle des événements, et je ne les ai pas essayés isolément.

## Autres éléments du domaine laissés non typés

- `domain/shared_kernel/events/` (12), `shared_kernel/excitation/events/` (4), `shared_kernel/motion/events/` (9) et `shared_kernel/value_objects/` (10) : `part_of` exige une racine d'agrégat, et `shared_kernel` n'en est pas une.
- `domain/detection_devices/**` (électrode, sonde inertielle, lidar, signal) : même question, plus l'imbrication `detection_devices/<x>/`.

## Choix à faire

1. Remonter `test_bench/calibration` en `domain/calibration` (un déplacement de dossier, imports suivis) : débloque 38 typages avec la règle de place satisfaite. Même question pour `detection_devices/**`.
2. Pour `shared_kernel`, décider si ses événements et objets-valeurs sont typés `atome` `regle-metier` (perd les contrôles D4 et D5) ou rattachés à un agrégat existant.
