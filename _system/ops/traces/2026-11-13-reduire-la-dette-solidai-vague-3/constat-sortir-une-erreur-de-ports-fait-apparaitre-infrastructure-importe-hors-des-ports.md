---
type: constat::sh-agent-os
genere_par: "[[tache - reduire la dette solidai vague 3]]"
doc_type: constat
date: 2026-11-13
---

# Sortir une erreur de `ports/` fait apparaître 6 erreurs `infrastructure-importe-hors-des-ports`

**Lot annulé (`git reset --hard`, rien commité).** Le geste de la fiche `geste-port-mal-nomme.md` fait baisser `solidai-port-mal-nomme` de 3 à 0, mais le verify total monte de 1 169 à 1 174 (+5) : 6 erreurs nouvelles de fond.

## Ce qui s'est passé

Le lot déplaçait `lidar_stream_error.py`, `motion_conversion_unavailable_error.py` et `raw_increment_motion_error.py` (et leurs intentions) de `<service>/ports/` vers `<service>/errors/`, imports suivis dans 23 fichiers.
Tant que l'erreur vivait dans `ports/`, la règle A14 (« l'infrastructure n'importe de l'application que ses ports ») laissait passer l'import par un adaptateur.
Dans `errors/`, l'import devient « ni un port ni un nom qu'un port nomme » : 6 nouveaux `solidai-infrastructure-importe-hors-des-ports` (3 adaptateurs et 3 Fakes de l'infrastructure).
Le reste du bilan : −3 `port-mal-nomme`, +2 `trio-incomplet` (deux nouveaux `errors/` sans `_tests/`), +3 `intention-non-typee` déplacées (0 net, les 3 anciennes disparaissent). pytest 1 707 verts, mypy 2 943 : le code est intact.

## Cause et suite

La fiche prévoyait le `trio-incomplet` sur `errors/`, pas A14.
C'est le point 4a d'`a-discuter-avec-l-humain.md` (la frontière d'import de l'infrastructure est plus stricte que sa source : Martin, *Clean Architecture*, ch. 22, les structures qui traversent la frontière sont connues des deux côtés).
Une erreur que le port déclare dans sa signature doit rester importable par l'adaptateur : la règle doit accepter les noms que la signature du port lève ou documente, ou la fiche doit garder l'erreur dans `ports/` jusque-là.

Le lot est à refaire après le changement d'outil de A14 (ou après la décision de l'humain sur le point 4a), sans autre jugement.
