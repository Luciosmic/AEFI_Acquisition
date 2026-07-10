# system_shutdown_complete_event — Intention

## Rationale

Modéliser la fin de la séquence d'arrêt du système comme un fait immuable passé, découplé de la UI et de l'infrastructure d'exécution.

## Responsibility

- `SystemShutdownCompleteEvent` : success + details — arrêt terminé.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
