# sphere_phases_dto — Intention

## Rationale

Isoler la couche interface des types `domain/` (`PhaseAngle`, `SphereId`, ...) utilisés en interne par `SynchronousDetectionService`. Seul cet objet doit traverser la frontière application → interface pour la fonctionnalité de détection synchrone.

## Responsibility

Porter les 4 phases dérivées des sphères S1-S4 (en degrés), le Delta_Phi corrigé courant (`None` si aucune donnée de calibration disponible pour la fréquence/signature matérielle courante), et l'état lecture-seule de l'enforcement de quadrature ch3/ch4.

## Design

- `@dataclass(frozen=True)` — DTO immuable, primitives uniquement (pas de VO domain).
- Construit par `SynchronousDetectionService.get_sphere_phases()`.
