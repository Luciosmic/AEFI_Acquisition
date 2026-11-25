---
type: constat::sh-agent-os
genere_par: "[[tache - migrer la memoire native vers les repos]]"
doc_type: constat
---

# Plan de synchro git continue entre machines, à porter dans sh-agent-os

Ce plan vivait dans la mémoire native de Claude du PC du labo, rattachée à GRAPHE-THESE.
Il relève de SOLIDHARNESS / sh-agent-os, dont les repos Dropbox sont en lecture seule pour git sur ce PC : il attend ici d'être porté depuis le Mac.
**Ne pas le mettre en œuvre sans que l'humain le relance.**

Le 2026-11-16, l'humain a retenu, à l'état de plan seulement, une « option 1 » pour rendre le graphe typé robuste en collaboratif.

- Une forge git (Gitea de l'équipe ou GitHub) sert de source de vérité pour chaque repo du graphe composé.
- Chaque machine a ses clones hors Dropbox et son propre démon Ars Umbris.
- Un petit service pousse après chaque commit du moteur et tire toutes les 10 à 30 s. Le gitwatch du moteur réintègre les commits venus d'ailleurs.
- Reste à décider : faut-il auto-commiter les éditions faites hors moteur (Obsidian) ?
- Ensuite : une validation du graphe sur la forge à chaque push, puis des branches par collaborateur ou agent.

L'option 2, un seul démon Ars Umbris dans le cloud, joint à distance par MCP en HTTP, est la cible à moyen terme.
Elle est à poser à l'équipe arsumbris, car le moteur 0.0.2 n'expose qu'un socket ou un pipe local.

Pourquoi : Dropbox recopie fichier par fichier, sans transaction, ce qui abîme les `.git` (le `.git` de GRAPHE-THESE sur ce PC en est un cas).
L'humain veut un moteur collaboratif et cloud au cœur de ses solutions, avec une synchro continue.
En attendant, la branche `windows-port` d'arsumbris continue d'aller sur Dropbox par `git push dropbox windows-port`.
