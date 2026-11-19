---
type: constat::sh-agent-os
genere_par: "[[tache - reduire la dette solidai vague 2]]"
doc_type: constat
tldr: "Les lots 14 et 16 passent tous les contrôles avant leur commit, mais leur commit change les avertissements de co-changement entre couches de verify ; ils sont défaits."
---

# Lots 14 et 16 annulés : leur commit déplace le co-changement entre couches

**Défaits après leur commit, sans aucun changement gardé.**
Avant commit, pytest, mypy et verify passent.
`solidai-co-changement-entre-couches` lit l'historique git : un commit de plus sur un fichier change ses rapports « change ensemble dans N commits sur M ».

- **Lot 14** (49 fonctions, domaine seul) : une fois commité, les avertissements passent de 63 à 69, avec 8 paires nouvelles et 2 disparues (`run-verify-head-apres-lot-14.json`). Par exemple, `excitation_level.py` et `i_excitation_port.py` « changent ensemble dans 4 commits sur 5 ».
  Le commit défait (`git reset --soft`, puis restauration des fichiers), verify revient à 63 (`run-verify-sans-commit-lot-14.json`).
- **Lot 16** (52 fonctions) : un premier essai a échoué sur les 6 avertissements du lot 14, alors encore commité. Rejoué après l'annulation du lot 14, son commit fait passer les avertissements de 63 à 61 (`run-verify-lot-16-commite-annule.json`). Il est défait de la même façon.

Le lot 15 a été commité puis contrôlé de la même façon : verify reste identique.

Ce signal mesure la forme des commits, pas le code.
Annoter des fichiers de plusieurs couches dans un même commit le fait bouger.
Pour reprendre ces lots, deux voies s'offrent :
- commiter un lot couche par couche
- laisser verify ignorer les commits d'annotation pure dans ce calcul
