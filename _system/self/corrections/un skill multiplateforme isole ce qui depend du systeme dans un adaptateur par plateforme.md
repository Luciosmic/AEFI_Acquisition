---
type: correction.open::au-govern
---
# What I did

Pour faire marcher le skill de rafraîchissement d'Ars Umbris sous Windows, j'allais ajouter les commandes Windows à côté des commandes Mac, dans le même fichier de déroulé.

# What they wanted

« Il faut que ce qui est propre à l'OS soit isolé pour pouvoir découpler la logique de l'infrastructure », « pattern hexagonal », avec « un diagnostic au démarrage pour reconnaître la plateforme ».

Le déroulé du skill nomme des opérations, sans aucune commande.
Les règles qui ne dépendent pas de la machine vont dans `domain/`.
Un contrat liste les opérations que chaque plateforme fournit, et un adaptateur par système (`macos.md`, `windows.md`) donne leurs commandes.
La première étape est un diagnostic qui reconnaît la plateforme et désigne l'adaptateur.
Chaque commande Windows est testée sur le PC avant d'être écrite.
