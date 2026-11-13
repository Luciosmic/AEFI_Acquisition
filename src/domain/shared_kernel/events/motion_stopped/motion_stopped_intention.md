---
type: evenement-de-domaine::solidai-ddd
tldr: "Événement `motion_stopped` : `reason` : motif de l'arrêt (ex. `\"scan_cancelled\"`, `\"user_requested\"`)."
code: ["[[src/domain/shared_kernel/events/motion_stopped/motion_stopped.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/shared_kernel/operation_result_intention]]"
---
# motion_stopped — Intention

## Rationale

Modéliser l'arrêt intentionnel (non urgent) d'un déplacement comme un fait immuable passé — arrêt avec décélération, par opposition à l'arrêt d'urgence.

## Responsibility

- `reason` : motif de l'arrêt (ex. `"scan_cancelled"`, `"user_requested"`).

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- Consommé par `StepScanExecutor` pour réveiller la boucle d'attente et interrompre le scan proprement.
