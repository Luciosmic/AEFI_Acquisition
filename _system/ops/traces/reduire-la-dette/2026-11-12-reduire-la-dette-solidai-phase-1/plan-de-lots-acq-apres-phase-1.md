---
doc_type: rapport
tldr: "Plan de lots de la dette SolidAI d'ACQ après la phase 1 réduite à trois exemples : 1 313 erreurs (1 314 avant), 131 lots dont 34 mécaniques (535 erreurs, 41 %). Les lots de typage des Fakes et 24 des 25 Fakes mal placés restent bloqués par le typage et la place des réels."
---

# Plan de lots d'ACQ après la phase 1

1. **Erreurs** : 1 314 avant, 1 313 après ; seul `solidai-fake-mal-place` baisse (26 → 25). Le plan d'origine du 2026-11-12 comptait 1 206 erreurs : la dette avait grossi de 108 avant la phase 1.
2. **Lots restants** : 131, dont 34 mécaniques, comme avant ; le lot 6 de `fake-mal-place` passe de 2 à 1 erreur.
3. **Part mécanique restante** : 535 erreurs sur 1 313, soit 41 %.
4. **Mécaniques en apparence seulement** : les lots 12 à 18 (typage des Fakes, 46 erreurs) et 24 des 25 erreurs `fake-mal-place` attendent le typage des réels et des ports, puis le déplacement des réels (H16) ; voir les deux constats du dossier.
5. **Seul cas mécanique restant de la famille** : `acquisition_conditions/fake/fake_acquisition_conditions_port.py`, à renommer comme l'exemple de provenance.

La sortie complète de `trier-la-dette.sh <ACQ> --format texte` (2 101 lignes) est dans `run-tri-apres-phase-1.txt`, à côté ; celle d'avant, dans `run-tri-avant.txt`.
