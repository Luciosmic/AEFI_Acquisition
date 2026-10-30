# motion_conversion_found_missing — Intention

## Rationale

Sans cet événement, l'absence de conversion mm/impulsion reste une ligne de log : le mouvement et le scan sont refusés sans que l'opérateur sache pourquoi, ni quelle grandeur saisir. L'état « non calibré » doit être un fait nommé que l'interface peut afficher.

## Responsibility

- `motor_name` : moteur monté concerné (`None` si aucun).
- `missing_quantity` : grandeur manquante, en toutes lettres (p. ex. « Pas par tour »).
- `where_to_enter` : où la saisir (panneau Calibration, onglet « Moteurs »).

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`, publié sous le topic `motionconversionfoundmissing`.
- Publié par `MotionConversionHandler` au démarrage et à chaque changement du manque ; relayé au tableau de bord par `MotionPresenter`.
- Contre-partie : `MotionConversionBecameAvailable`.
