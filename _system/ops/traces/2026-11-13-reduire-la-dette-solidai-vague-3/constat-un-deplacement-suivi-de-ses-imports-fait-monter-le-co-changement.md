---
type: constat::sh-agent-os
genere_par: "[[tache - reduire la dette solidai vague 3]]"
doc_type: constat
date: 2026-11-13
---

# Un déplacement et ses imports dans un seul commit font monter `co-changement-entre-couches`

**À discuter, aucun lot annulé.** Le lot 2 (`domain_event` et `i_domain_event_bus` dans leur dossier d'événement) fait passer les avertissements `solidai-co-changement-entre-couches` de 55 à 84 une fois commité, alors que verify, pytest et mypy sont bons avant commit.

## Cause

`DomainEvent` est importé par 139 fichiers de toutes les couches.
Le commit qui suit ces imports touche donc des fichiers du domaine, de l'application, de l'infrastructure et de l'interface à la fois, et `solidai-co-changement-entre-couches` lit l'historique git : chaque paire de couches qui « change ensemble » dans ce commit gagne un point.
Le commit unique est imposé : séparer le déplacement et le suivi des imports casse l'import dans le commit intermédiaire (règle de la tâche : chaque commit passe seul).

Ce n'est pas une erreur (les avertissements ne sont pas comptés dans `errors`), et la vague 2 avait défait deux lots de typage pour un effet de ce genre, mais un lot de typage se découpe couche par couche et un déplacement avec ses imports ne se découpe pas.
Les lots suivants qui suivent des imports dans plusieurs couches feront monter ce compteur de la même façon.

## Autre effet à signaler

`src/domain/step_scan/events/electric_field_scan_point_acquired/electric_field_scan_point_acquired.py` (dossier non suivi, non touché) importe l'ancien chemin `domain.shared_kernel.events.domain_event`.
Quand l'humain le commitera, il y suit l'import : `domain.shared_kernel.events.domain_event.domain_event`.

## Choix à faire

1. Garder les déplacements en un seul commit et laisser le compteur monter (il se dilue à mesure que les commits s'accumulent).
2. Faire ignorer à la règle les commits qui ne font que suivre un déplacement : changement d'outil, hors de cette vague.
