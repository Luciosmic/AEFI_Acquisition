# motion_conversion_became_available — Intention

## Rationale

Sans cet événement, un bandeau « non calibré » resterait affiché après la saisie de la grandeur manquante, ou l'interface devrait sonder le service : la fin de l'état non calibré doit être un fait publié.

## Responsibility

- `microns_per_pulse` : distance par impulsion appliquée au port de mouvement (µm).
- `motor_name`, `stepper_driver_name` : composants montés dont elle découle.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`, publié sous le topic `motionconversionbecameavailable`.
- Publié par `MotionConversionHandler` après `set_microns_per_pulse` (au démarrage si déjà calibré, ou en direct après la saisie).
