# physical_units — Intention

## Rationale

Définir les constantes et conversions d'unités physiques utilisées dans le domain AEFI (mm, µm, Hz, V, rad…). Centraliser ces définitions évite la multiplication de constantes magiques dispersées dans le code.

## Responsibility

- Définir les unités et facteurs de conversion pertinents pour le système d'acquisition AEFI.
- Servir de référence unique pour les conversions entre unités dans le domain et les services.

## Design

- **Module de constantes** dans `domain/shared/` : pas d'instances, pas de classes instanciables.
- Utilisé par les value objects et services qui expriment des grandeurs physiques.
