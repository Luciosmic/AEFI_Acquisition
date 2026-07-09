# column — Intention

## Rationale

Value object représentant une colonne physique du banc d'essai, qui porte une ou plusieurs sources de champ électrique à des hauteurs définies. La colonne est l'unité structurale du banc.

## Responsibility

- Stocker l'identifiant de la colonne, sa position X dans le banc, et la liste des sources qu'elle porte.

## Design

- **`@dataclass(frozen=True)`** : une colonne est une configuration physique fixe pendant une expérience.
- Utilisé par `TestBench.configure_geometry()`.
