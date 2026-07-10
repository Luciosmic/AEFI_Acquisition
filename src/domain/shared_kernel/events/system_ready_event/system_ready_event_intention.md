# system_ready_event — Intention

## Rationale

Modéliser le cycle de vie global du système (démarrage) comme un événement domain. Permet à la UI et aux services de réagir aux transitions système sans couplage direct avec le service lifecycle.

## Responsibility

- `SystemReadyEvent` : le système est initialisé et prêt pour les opérations.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
