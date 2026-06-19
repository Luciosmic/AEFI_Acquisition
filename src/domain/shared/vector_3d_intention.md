# vector_3d (domain/shared) — Intention

## Rationale

Value object vectoriel 3D partagé entre les services domain (physique AEFI, géométrie du banc). Version dans `domain/shared/` vs `domain/value_objects/geometric/` : ce sont les implémentations utilisées directement par les agrégats domain (AefiDevice, calcul d'interactions).

## Responsibility

- Représenter un vecteur 3D (x, y, z) avec les opérations algébriques nécessaires (addition, soustraction, norme, produit scalaire/vectoriel).

## Design

- **Immuable** (`frozen=True`) : la physique domain ne doit pas modifier un vecteur en place.
- Opérateurs `__sub__`, `__add__` pour la syntaxe lisible des calculs géométriques.
