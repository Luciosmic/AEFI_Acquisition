---
type: constat::sh-agent-os
genere_par: "[[tache - reduire la dette solidai phase 1]]"
doc_type: constat
tldr: "Sur les 26 erreurs fake-mal-place d'ACQ, 24 ne se corrigent pas en déplaçant le Fake seul : H18 veut infrastructure/<adaptateur>/fake/fake_<adaptateur>.py, et les réels d'ACQ vivent à deux niveaux (hardware/…, persistence/…) ou à plusieurs par dossier (events/, execution/). Il faut d'abord déplacer les réels (H16)."
---

# fake-mal-place : 24 cas sur 26 exigent de déplacer le réel

**Verdict : 2 cas mécaniques, 24 bloqués.** Le geste « déplacer le Fake sous le fake/ du dossier de son réel » ne suffit que là où le dossier d'infrastructure tient un seul réel, au premier niveau.

## La forme que la vérification attend

La vérification `solidai-fake-mal-place` (solidai-hexagonal, `checks/domain/hexagonal_code.py`) accepte un Fake seulement à `infrastructure/<A>/fake/fake_<A>.py` : trois segments sous `infrastructure/`, et le nom du Fake égal à `fake_` plus le nom du dossier.

## Les trois cas d'ACQ

| Cas | Fakes | Ce qu'il faudrait |
|---|---|---|
| Réel à deux niveaux (`hardware/<appareil>/`, `persistence/<sujet>/`) | 20 | sortir chaque réel au premier niveau d'`infrastructure/`, avec ses imports : c'est le lot `adaptateur-mal-place` (H16) |
| Dossier à plusieurs réels (`events/`, `execution/`) | 4 | un dossier par réel, puis le Fake dans son `fake/` |
| Dossier à un seul réel (`acquisition_conditions/`, `provenance/`) | 2 | renommer le Fake en `fake_<dossier>.py`, son intention avec, et suivre ses imports |

Déplacer le Fake seul vers un dossier neuf ferait taire la vérification en éloignant le Fake de son réel, l'inverse de H18.
Les 20 cas sous `hardware/` comprennent `arcus_performax_4EX/`, que le lot snake_case, exclu de la phase 1, renomme aussi.

## Proposition

Traiter `adaptateur-mal-place` (66 erreurs) avant `fake-mal-place`, sur décision de l'humain, car le réel fixe la place de son Fake.
