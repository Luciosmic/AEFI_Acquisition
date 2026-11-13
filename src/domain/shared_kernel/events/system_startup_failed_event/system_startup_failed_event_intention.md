---
type: evenement-de-domaine::solidai-ddd
tldr: "`SystemStartupFailedEvent` : reason string — l'initialisation a échoué."
code: ["[[src/domain/shared_kernel/events/system_startup_failed_event/system_startup_failed_event.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/shared_kernel/operation_result_intention]]"
---
# system_startup_failed_event — Intention

## Rationale

Modéliser l'échec du démarrage du système comme un fait immuable passé, découplé de la UI et de l'infrastructure d'exécution.

## Responsibility

- `SystemStartupFailedEvent` : reason string — l'initialisation a échoué.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
