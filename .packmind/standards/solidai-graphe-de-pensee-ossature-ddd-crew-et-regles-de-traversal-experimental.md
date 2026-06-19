# SolidAI — Graphe de Pensée : Ossature DDD-Crew et Règles de Traversal [EXPÉRIMENTAL]

⚠️ STATUT EXPÉRIMENTAL — Ces règles sont en cours de validation et peuvent évoluer. Ce standard définit l'ossature du graphe de pensée SolidAI en trois couches de stabilité décroissante (#domain, #application, #infra), calquées sur les 8 étapes du DDD Starter Modelling Process (ddd-crew). Il gouverne l'ordre de création des nœuds, la direction des liens, et les conditions de modification. L'agent traverse toujours du stable vers le volatile, et ne crée jamais une couche inférieure sans ancrage dans la couche supérieure. Référence : https://github.com/ddd-crew/ddd-starter-modelling-process

## Rules

* Mapper chaque nœud à exactement une couche de stabilité : #domain (étapes Understand/Discover), #application (étapes Decompose/Strategize/Connect), #infra (étapes Define/Code) — tout nœud sans tag de couche est invalide.
* Respecter l'ordre d'apparition des couches : un nœud #application requiert au moins un nœud #domain parent dans le même bounded context ; un nœud #infra requiert au moins un nœud #application parent.
* Orienter tous les liens du volatile vers le stable (#infra → #application → #domain), jamais dans le sens inverse.
* Ne modifier un nœud #domain qu'après validation utilisateur explicite, en traçant la source de la modification (S_user, S_retroing ou S_doc) — la discovery est continue mais toute modification de couche stable est auditée.
