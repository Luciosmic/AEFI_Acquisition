---
type: constat::sh-agent-os
genere_par: "[[tache - typer les traces du post traitement]]"
---

# Une note de tâche ne relie qu'une étape : celle par laquelle la tâche commence

Le champ `etape` d'une tâche vise une seule étape, lue par le générateur dans le premier `etape=` d'une ligne `depart` de la trace. Les trois tâches de la tranche 1 couvrent chacune plusieurs étapes.

- `tranche 1 etapes 1 0 a 1 3` relie `etape-1-0` (sa trace couvre en fait 1.0 à 1.5) ;
- `tranche 1 etapes 1 6 et 1 7` relie `etape-1-6` ;
- `tranche 1 etapes 1 8 et 1 9` relie `etape-1-8`.

Pour cela, `| etape=<id>` a été ajouté à la fin de la première ligne `depart` de ces trois traces. Dans la trace 1.0–1.3, l'ancienne ligne `depart | etape=1.5 catalogue…` reste telle quelle : le générateur garde le premier `etape=` et ignore celle-ci, ce qui supprime l'alerte « étape absente du plan ».

Les tâches `concevoir l architecture par panneaux` (étape 2 du plan, en prose) et `avis solidai sur la conception` n'ont pas d'étape déclarée : le plan ne déclare que 1.0 à 1.9.

À lever par : si l'on veut un lien par étape, découper la trace en une tâche par étape ou regrouper les étapes en molécules.
