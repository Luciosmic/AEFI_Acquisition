# scan_progress — Intention

## Rationale

Value object représentant l'avancement courant d'un scan (points acquis / total). Séparer ce calcul du `ScanStatusDTO` (applicatif) permet de l'utiliser directement dans les événements domain si nécessaire.

## Responsibility

- Stocker le nombre de points acquis et le total attendu.
- Calculer le pourcentage de progression.

## Design

- **`@dataclass(frozen=True)`** avec propriété `percentage`.
- Léger, aucune dépendance externe.
