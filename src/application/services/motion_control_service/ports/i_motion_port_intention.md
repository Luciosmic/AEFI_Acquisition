# i_motion_port — Intention

## Rationale

Abstraire le contrôleur moteur physique (Arcus Performax 4EX) derrière un port domain-agnostique. Permet de tester la logique de motion sans le hardware et de substituer le contrôleur sans modifier les services applicatifs.

## Responsibility

- Déclarer `move_to(position: Position2D) → str` (retourne un motion_id pour la synchronisation event-based).
- Déclarer `stop()`, `emergency_stop()`, `home(axis)`, `get_current_position()`, `set_reference(axis, position)`, `get_axis_limits()`.

## Design

- **Port outbound** co-localisé dans `motion_control_service/`.
- `move_to` retourne un `motion_id` (str) utilisé par `StepScanExecutor` pour la synchronisation event-based (`MotionCompleted.motion_id`).
- Implémenté par `AdapterMotionPortArcusPerformax4EX` (Real) et `AdapterMockIMotionPort` (Mock).
