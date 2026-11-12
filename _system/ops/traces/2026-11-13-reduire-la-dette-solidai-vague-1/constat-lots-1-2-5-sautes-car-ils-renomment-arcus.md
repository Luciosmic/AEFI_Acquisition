---
type: constat::sh-agent-os
genere_par: "[[tache - reduire la dette solidai vague 1]]"
doc_type: constat
tldr: "Les lots 1, 2 et 5 du tri ne sont pas faits : chacun renomme un chemin sous arcus_performax_4EX, que la vague 1 exclut parce que le chargement de la DLL du fabricant peut dépendre de ce chemin."
---

# Lots 1, 2 et 5 sautés : ils renomment des chemins d'arcus_performax_4EX

**Sautés, sans aucun changement.**
La consigne de la vague 1 exclut tout lot qui renomme un chemin de `src/infrastructure/hardware/arcus_performax_4EX/` ou touche un `.dll`, `.lib` ou `.h` du fabricant.

- **Lot 1** (`solidai-chemin-hors-snake-case`, 47 erreurs) : 45 erreurs viennent du dossier `arcus_performax_4EX` lui-même (le `4EX` majuscule), dont `DLL64/PerformaxCom.dll`, `.h`, `.lib` et `SiUSBXp.dll`. Les 2 autres sont des diagrammes `… copy.puml` de `_system/documentation/diagrams/`, sans risque, mais le lot se prend entier.
- **Lot 2** (même code, 13 erreurs) : 7 erreurs sous `arcus_performax_4EX/fake/`, 6 dans `micro_controller/` (`MCU_serial_communicator`, `adapter_lifecycle_MCU`).
- **Lot 5** (`solidai-intention-mal-nommee`, 4 erreurs) : `arcus_performax_4EX/_tests/uncalibrated_transmission_intention.md` en fait partie.

Renommer `arcus_performax_4EX` en `arcus_performax_4ex` règle d'un coup la plupart des 60 erreurs `chemin-hors-snake-case`.
Avant, il faut vérifier comment `driver_arcus_performax4EX.py` trouve `DLL64/` (chemin relatif à `__file__`, variable d'environnement, ou chemin écrit en dur), puis le tester sur le banc sous Windows.

Les diagrammes `… copy.puml` et les fichiers `micro_controller/` peuvent former un lot à part, hors d'arcus, si le tri les sépare.
