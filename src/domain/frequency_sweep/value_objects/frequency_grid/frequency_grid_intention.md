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
- `logarithmic(start, stop, count)` : `count` fréquences de `start` à `stop` inclus, en espacement logarithmique.
- `index_of(f)` : rang d'une fréquence de la grille.

## Design

- `@dataclass(frozen=True)`, tuple de flottants ; égalité par valeur, pour que deux grilles construites des mêmes bornes soient égales.
- Fréquences arrondies au millihertz : la quantification du DDS (16 MHz / 2³², environ 4 mHz) rend inutile toute précision au-delà.
- Les bornes du générateur ne sont pas vérifiées ici : c'est une contrainte du matériel, pas de la grille.
- Domaine pur.
