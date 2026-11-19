---
doc_type: rapport
tldr: "Vague 2 : DLL64 exclu, arcus_performax_4EX renommé en arcus_performax_4ex, 11 lots de typage mécaniques faits sur 15 ; verify 1266 -> 1215 erreurs, mypy 3298 -> 2943, tests identiques."
---

# Bilan de la vague 2

- **verify** : 1 266 → 1 215 erreurs (−5 par l'exclusion de `DLL64/`, −46 par le renommage du paquet), 63 avertissements avant et après. **mypy** : 3 298 → 2 943 erreurs ; `no-untyped-def` 2 864 → 2 401 (−463), et 108 erreurs anciennes révélées dans les corps désormais vérifiés.
- **Lots de typage** : 11 faits (3, 5 à 13, 15) ; 2 annulés pour un code mypy nouveau, `list-item` (2 et 4) ; 2 défaits parce que leur commit déplace le co-changement entre couches (14 et 16) ; aucun sauté.
- **Mécaniques restants** : 1 lot verify (9 erreurs `chemin-hors-snake-case`, hors d'arcus) et 21 lots de typage (1 291 erreurs) (`run-tri-apres.txt`).
- **Tests** : `pytest src` reste à 1 707 réussis et 3 sautés à chaque étape ; le test de moyennage instable sous charge a été rejoué seul une fois, au lot 2.
- **Pour l'humain** : lancer une fois l'application sur le banc Windows pour confirmer que la DLL du fabricant se charge toujours depuis `arcus_performax_4ex/DLL64/`.

Détail : `trace.log` et les trois constats de ce dossier.
