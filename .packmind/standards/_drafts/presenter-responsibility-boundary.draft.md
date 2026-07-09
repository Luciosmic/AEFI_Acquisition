# Presenter Responsibility Boundary

Presenters in `src/interface/presenters/` act as the glue between application services and Qt views. They have a dual role: implementing the output port (service → presenter) and handling Qt slots (view → presenter). Business logic must not cross into the presenter layer.

Evidence: `src/interface/presenters/scan_presenter.py:75-110` (ETA calculation logic — borderline business logic in presenter), `src/interface/presenters/motion_presenter.py`, `src/interface/presenters/hardware_advanced_config_presenter.py`

## Scope

Python files under `src/interface/presenters/` matching `*_presenter.py`.

## Rules

- Inherit from both `QObject` and the corresponding output port interface (e.g., `IScanOutputPort`)
- Emit Qt signals in output port implementation methods — do not manipulate view state directly
- Handle user actions via `@Slot` methods that forward to the application service — no domain logic in slots
- Avoid stateful computation that derives business values (e.g., ETA, averages) — delegate to the service instead
- Register as output port via `service.set_output_port(self)` in `__init__`, not lazily
- Do not import from `domain/` directly — use DTOs from `application/dtos/`
