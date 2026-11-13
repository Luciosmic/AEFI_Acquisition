---
type: evenement-de-domaine::solidai-ddd
tldr: "`SystemShutdownCompleteEvent` : success + details — arrêt terminé."
code: ["[[src/domain/shared_kernel/events/system_shutdown_complete_event/system_shutdown_complete_event.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/shared_kernel/operation_result_intention]]"
---
# system_shutdown_complete_event — Intention

## Rationale

Modéliser la fin de la séquence d'arrêt du système comme un fait immuable passé, découplé de la UI et de l'infrastructure d'exécution.

## Responsibility

- `SystemShutdownCompleteEvent` : success + details — arrêt terminé.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
