---
type: value-object::solidai-ddd
tldr: "Porter les fréquences d'excitation d'un balayage, en Hz : au moins 2, finies, strictement positives, strictement croissantes."
code: ["[[src/domain/frequency_sweep/value_objects/frequency_grid/frequency_grid.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/frequency_sweep/frequency_sweep_intention]]"
---
# frequency_grid — Intention

## Rationale

Deux balayages ne se comparent, ne se soustraient et ne se combinent que fréquence par fréquence, sur la même grille. Une grille saisie à la main, avec un doublon ou une fréquence nulle, produirait un balayage incomparable sans que rien ne le signale.

## Responsibility

- Porter les fréquences d'excitation d'un balayage, en Hz : au moins 2, finies, strictement positives, strictement croissantes.
- `per_decade(start, stop, n)` : les fréquences 10^(k/n) Hz (k entier) comprises entre `start` et `stop` inclus.
- `from_list(fréquences)` : les fréquences données par l'opérateur, balayées par ordre croissant ; un doublon est refusé.
- `index_of(f)` : rang d'une fréquence de la grille.

## Design

- `@dataclass(frozen=True)`, tuple de flottants ; égalité par valeur, pour que deux grilles construites des mêmes bornes soient égales.
- Les points par décade sont ancrés sur les puissances de 10, pas sur les bornes : deux grilles de même densité partagent toutes leurs fréquences communes, quelles que soient leurs bornes, et un fond acquis sur une large plage se soustrait à une mesure objet acquise sur une partie de cette plage. Une borne qui n'est pas un point de la décade n'est donc pas balayée : le premier point est celui qui la suit.
- Une liste est triée plutôt que refusée dans le désordre : l'ordre de saisie ne porte pas de sens, et l'agrégat exige une grille croissante.
- Fréquences arrondies au millihertz : la quantification du DDS (16 MHz / 2³², environ 4 mHz) rend inutile toute précision au-delà.
- Les bornes du générateur ne sont pas vérifiées ici : c'est une contrainte du matériel, pas de la grille.
- Domaine pur.
