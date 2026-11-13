---
type: constat::sh-agent-os
genere_par: "[[tache - reduire la dette solidai vague 5 suite]]"
doc_type: constat
statut: to_validate
---

# Les intentions de ports restent comptées « non typées » par A20

**Constat** : 40 intentions de ports d'application (`ports/i_*_intention.md`, `i_api_*_intention.md`) portent bien un type (`port::solidai-hexagonal`), et 11 intentions d'interfaces de repository du domaine sont dans le même cas, mais la vérification `solidai-intention-non-typee` ne compte que `atome` et ses sous-types, pas `port`. Elles restent donc dans l'erreur A20 (51 sur les 120 restantes).

Les ports déjà typés ainsi avant la vague (`i_software_provenance_port_intention.md`) sont dans le même cas. Le type `service-applicatif` refuse en plus une liste `ports:` de liens vers ces fichiers : il attend des enregistrements `^:` inline (le moteur donnait 33 erreurs, retirées au commit `d7cfc64f`).

## Deux voies

1. **Ajouter `port` et `interface-de-repository` aux types que A20 accepte** (paramètre `types` de `solidai-intention-non-typee` dans solidai-atome). Une ligne de configuration, aucune note à toucher. Les ports gardent leur intention propre, ce que H5 déconseille (« le port n'a pas d'intention propre : sa docstring en tient lieu »).
2. **Suivre H5 jusqu'au bout** : copier Responsibility, Rationale et Design de chaque intention de port dans la docstring de sa classe, déclarer le port en enregistrement inline dans `ports:` de son service, supprimer le fichier. 51 fichiers, du texte français réécrit en docstrings anglaises, et la prose des intentions disparaît.

Recommandation : la voie 1 maintenant (elle débloque `implements` tel que le lot l'a écrit), la voie 2 service par service quand on touche à un port.
