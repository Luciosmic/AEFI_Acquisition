---
name: 'SolidAI — Graphe de Pensée : Ossature DDD-Crew et Règles de Traversal [EXPÉRIMENTAL]'
alwaysApply: true
description: 'Structurer les nœuds du graphe de pensée en trois couches de stabilité calquées sur le DDD Starter Modelling Process, et guider l''agent dans sa traversée du stable vers le volatile.'
---

# Standard: SolidAI — Graphe de Pensée : Ossature DDD-Crew et Règles de Traversal [EXPÉRIMENTAL]

Structurer les nœuds du graphe de pensée en trois couches de stabilité calquées sur le DDD Starter Modelling Process, et guider l'agent dans sa traversée du stable vers le volatile. :
* Mapper chaque nœud à exactement une couche de stabilité : #domain (étapes Understand/Discover), #application (étapes Decompose/Strategize/Connect), #infra (étapes Define/Code) — tout nœud sans tag de couche est invalide.
* Ne modifier un nœud #domain qu'après validation utilisateur explicite, en traçant la source de la modification (S_user, S_retroing ou S_doc) — la discovery est continue mais toute modification de couche stable est auditée.
* Orienter tous les liens du volatile vers le stable (#infra → #application → #domain), jamais dans le sens inverse.
* Respecter l'ordre d'apparition des couches : un nœud #application requiert au moins un nœud #domain parent dans le même bounded context ; un nœud #infra requiert au moins un nœud #application parent.

Full standard is available here for further request: [SolidAI — Graphe de Pensée : Ossature DDD-Crew et Règles de Traversal [EXPÉRIMENTAL]](../../../.packmind/standards/solidai-graphe-de-pensee-ossature-ddd-crew-et-regles-de-traversal-experimental.md)