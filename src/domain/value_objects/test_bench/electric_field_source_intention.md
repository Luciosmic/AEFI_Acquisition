# electric_field_source — Intention

## Rationale

Value object représentant une source de champ électrique (électrode) du banc d'essai. Porte les propriétés géométriques (position dans la colonne) et les caractéristiques d'excitation pertinentes pour le modèle physique.

## Responsibility

- Stocker : identifiant source, position Z dans la colonne, surface d'électrode, canal d'excitation associé.

## Design

- **`@dataclass(frozen=True)`** : une source est une configuration physique fixe.
- Portée par `Column` dans la hiérarchie `TestBench → Column → ElectricFieldSource`.
