# quaternion (domain/shared) — Intention

## Rationale

Value object représentant une rotation 3D par quaternion unitaire. Utilisé par `AefiDevice` pour exprimer l'orientation du capteur dans le repère de la sonde.

## Responsibility

- Stocker (w, x, y, z) et vérifier la norme unitaire.
- Fournir les opérations de composition de rotations et de transformation de vecteurs.

## Design

- **Immuable** (`frozen=True`).
- Placé dans `domain/shared/` pour être accessible depuis les agrégats domain et les services physics.
