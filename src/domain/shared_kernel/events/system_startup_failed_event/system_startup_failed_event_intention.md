# system_startup_failed_event — Intention

## Rationale

Modéliser l'échec du démarrage du système comme un fait immuable passé, découplé de la UI et de l'infrastructure d'exécution.

## Responsibility

- `SystemStartupFailedEvent` : reason string — l'initialisation a échoué.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
