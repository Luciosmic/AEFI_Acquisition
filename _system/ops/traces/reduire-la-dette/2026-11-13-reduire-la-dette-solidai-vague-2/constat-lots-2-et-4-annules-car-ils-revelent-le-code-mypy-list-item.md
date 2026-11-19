---
type: constat::sh-agent-os
genere_par: "[[tache - reduire la dette solidai vague 2]]"
doc_type: constat
tldr: "Les lots de typage 2 et 4 sont annulés : annoter leurs fonctions fait vérifier leur corps, et mypy y trouve des erreurs list-item, un code absent jusque-là."
---

# Lots 2 et 4 annulés : ils révèlent le code mypy `list-item`

**Annulés, sans aucun changement gardé.**
Leurs annotations sont justes : `no-untyped-def` baisse exactement du nombre du lot (63 pour le lot 2, 41 pour le lot 4).
Mais mypy ne vérifie le corps d'une fonction qu'une fois qu'elle est annotée.
Il y trouve alors des erreurs anciennes, dont `list-item`, un code qui n'existait pas dans la référence.
La consigne refuse tout code mypy nouveau : le lot est annulé.

- **Lot 2** : 30 erreurs révélées, dont 3 `list-item` (`run-mypy-lot-2-annule.log`)
- **Lot 4** : 7 erreurs révélées, dont 2 `list-item` (`run-mypy-lot-4-annule.log`)

Les lots faits révèlent eux aussi des erreurs, mais d'un code déjà présent : 108 en tout sur les 11 lots, surtout `attr-defined`, `union-attr`, `arg-type` et `var-annotated`.
Le critère lu à la lettre les laisse passer.

Pour reprendre ces deux lots, il faut d'abord corriger les erreurs `list-item` des corps concernés, ce qui est un travail de jugement.
