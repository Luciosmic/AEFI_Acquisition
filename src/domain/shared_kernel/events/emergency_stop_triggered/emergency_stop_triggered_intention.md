---
type: evenement-de-domaine::solidai-ddd
tldr: "Événement `emergency_stop_triggered` : Aucun champ : le fait seul de l'occurrence suffit (via `occurred_on` hérité de `DomainEvent`)."
code: ["[[src/domain/shared_kernel/events/emergency_stop_triggered/emergency_stop_triggered.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/shared_kernel/operation_result_intention]]"
---
# emergency_stop_triggered — Intention

## Rationale

Modéliser le déclenchement d'un arrêt d'urgence comme un fait immuable passé — signal critique déclenchant l'annulation immédiate du scan en cours.

## Responsibility

- Aucun champ : le fait seul de l'occurrence suffit (via `occurred_on` hérité de `DomainEvent`).

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`, sans champ propre.
- Consommé par `StepScanExecutor` pour annuler immédiatement le scan en cours.
