---
type: evenement-de-domaine::solidai-ddd
tldr: "Événement `motion_conversion_became_available` : `microns_per_pulse` : distance par impulsion appliquée au port de mouvement (µm)."
code: ["[[src/domain/shared_kernel/events/motion_conversion_became_available/motion_conversion_became_available.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/shared_kernel/operation_result_intention]]"
---
# motion_conversion_became_available — Intention

## Rationale

Sans cet événement, un bandeau « non calibré » resterait affiché après la saisie de la grandeur manquante, ou l'interface devrait sonder le service : la fin de l'état non calibré doit être un fait publié.

## Responsibility

- `microns_per_pulse` : distance par impulsion appliquée au port de mouvement (µm).
- `motor_name`, `stepper_driver_name` : composants montés dont elle découle.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`, publié sous le topic `motionconversionbecameavailable`.
- Publié par `MotionConversionHandler` après `set_microns_per_pulse` (au démarrage si déjà calibré, ou en direct après la saisie).
