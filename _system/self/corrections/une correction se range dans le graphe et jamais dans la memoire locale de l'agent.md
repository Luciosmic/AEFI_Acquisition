---
type: correction.open::au-govern
---
# Une correction se range dans le graphe, jamais dans la mémoire locale de l'agent

## What I did

J'ai enregistré la consigne de l'humain sur les adaptateurs par plateforme dans la mémoire locale de l'agent, un fichier hors du repo que seules mes sessions sur ce PC relisent.

## What they wanted

« N'as-tu pas reçu la règle injectée au début de session qui te demande de ne pas utiliser ton système de mémoire local ? »

Une correction se range comme correction dans `_system/self/corrections/` du workspace, par le gate, et s'applique dans le même tour.
Ce qui a une valeur durable va dans le graphe, que les autres sessions et les autres machines lisent, pas dans une mémoire propre à l'agent.
