---
name: 'Presenter Responsibility Boundary'
alwaysApply: true
description: 'Presenter Responsibility Boundary'
---

# Standard: Presenter Responsibility Boundary

Presenters in `src/interface/presenters/` act as the glue between application services and Qt views. They have a dual role: implementing the output port (service → presenter) and handling Qt slots (vi... :
* Avoid stateful computation that derives business values (e.g., ETA, averages) — delegate to the service instead
* Do not import from `domain/` directly — use DTOs from `application/dtos/`
* Emit Qt signals in output port implementation methods — do not manipulate view state directly
* Handle user actions via `@Slot` methods that forward to the application service — no domain logic in slots
* Inherit from both `QObject` and the corresponding output port interface (e.g., `IScanOutputPort`)
* Register as output port via `service.set_output_port(self)` in `__init__`, not lazily

Full standard is available here for further request: [Presenter Responsibility Boundary](../../../.packmind/standards/presenter-responsibility-boundary.md)