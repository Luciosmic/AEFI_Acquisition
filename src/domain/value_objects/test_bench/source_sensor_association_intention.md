# source_sensor_association — Intention

## Rationale

Value object définissant l'association entre une source de champ électrique et le capteur — le "câblage logique" du banc. Rendre cette association explicite dans le domain permet de générer automatiquement les paires d'interaction et de configurer l'excitation sélective.

## Responsibility

- Stocker l'identifiant de la source et l'identifiant du capteur associé.
- Optionnellement, stocker le canal d'excitation et le poids de couplage.

## Design

- **`@dataclass(frozen=True)`**.
- Utilisé dans `TestBench.configure_geometry()` pour alimenter `recompute_interactions()`.
