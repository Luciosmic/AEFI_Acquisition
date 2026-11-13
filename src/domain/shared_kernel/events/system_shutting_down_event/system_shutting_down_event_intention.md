---
type: evenement-de-domaine::solidai-ddd
tldr: "`SystemShuttingDownEvent` : arrêt en cours — signal pour que les services actifs s'arrêtent proprement."
code: ["[[src/domain/shared_kernel/events/system_shutting_down_event/system_shutting_down_event.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/shared_kernel/operation_result_intention]]"
---
# system_shutting_down_event — Intention

## Rationale

Modéliser le début de la séquence d'arrêt du système comme un événement domain. Signal pour que les services actifs s'arrêtent proprement, sans couplage direct avec le service lifecycle.

## Responsibility

- `SystemShuttingDownEvent` : arrêt en cours — signal pour que les services actifs s'arrêtent proprement.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- Publié AVANT les opérations d'arrêt : donne aux services l'opportunité de se nettoyer en réaction à l'événement.
