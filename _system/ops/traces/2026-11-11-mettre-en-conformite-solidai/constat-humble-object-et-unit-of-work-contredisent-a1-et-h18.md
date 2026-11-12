---
doc_type: constat
statut: to_validate
---

# Deux des 7 standards contredisent une règle du paquet autre qu'A12

La tâche s'est arrêtée là, comme le prompt le demandait.
Les 6 autres standards et l'affinement d'A12 sont écrits et commités.
La phase 2 dans AEFI_Acquisition n'a pas commencé : retirer Packmind maintenant ferait perdre le standard Humble Object, qui n'a pas encore de foyer.

## Humble Object contre A1 : en attente

**A1** (solidai-atome) : tout dossier qui tient un module Python tient aussi un `_tests/` non vide.

**Humble Object** (`solidai-qt-widget-humble-object-vue-sans-logique.md`) : un `_tests/` vide est correct pour une vue qui passe le test du Humble Object, et on ne teste pas la mise en page.

Les deux ne tiennent pas ensemble pour un widget.
Choix possibles :
- A. Le standard cède à A1 : le `_tests/` d'une vue tient au moins un test de câblage, par exemple « la vue relaie l'action au presenter »
- B. A1 s'affine : une vue humble n'a pas de trio propre, comme `ports/` et `dtos/`, et ses tests vivent avec son presenter
- C. Le standard garde son `_tests/` vide, et l'écart à A1 s'inscrit dans son texte comme exception nommée

Recommandation : B.
Le Humble Object dit justement que la vue n'a rien à tester, et A1 range déjà les dossiers sans comportement propre hors du trio.

## Unit of Work contre H18 : tranché par la règle de l'index, à confirmer

La source rangeait le Fake du Unit of Work avec l'interface, dans `application/`.
H18 range un Fake près de son réel, dans `infrastructure/<adaptateur>/fake/`, et A13 n'autorise un test applicatif qu'à importer ces Fakes-là.
L'index hors types fait céder un standard à une règle A, H ou D, comme pour « Test Mock Placement », qui cède à H18.
Le standard écrit suit donc H18.
Le défaire ne touche qu'une règle du fichier `standards/solidai-unit-of-work-abstraction-des-operations-atomiques.md` de solidai-developpement.
