---
name: 'Presenter Responsibility Boundary'
alwaysApply: true
description: 'Enforce a Presenter Responsibility Boundary for Python Qt presenters in `src/interface/presenters/*_presenter.py` by inheriting from `QObject` and the service output port, emitting Qt signals in output-port methods, handling `@Slot` user actions by forwarding to application services, registering via `service.set_output_port(self)` in `__init__`, and avoiding domain imports and business computations (e.g., ETA) to keep UI glue thin and business logic testable and maintainable.'
---

# Standard: Presenter Responsibility Boundary

Enforce a Presenter Responsibility Boundary for Python Qt presenters in `src/interface/presenters/*_presenter.py` by inheriting from `QObject` and the service output port, emitting Qt signals in output-port methods, handling `@Slot` user actions by forwarding to application services, registering via `service.set_output_port(self)` in `__init__`, and avoiding domain imports and business computations (e.g., ETA) to keep UI glue thin and business logic testable and maintainable. :
* Avoid stateful computation that derives business values (e.g., ETA, averages) — delegate to the service instead
* Do not import from `domain/` directly — use DTOs from `application/dtos/`
* Emit Qt signals in output port implementation methods — do not manipulate view state directly
* Handle user actions via `@Slot` methods that forward to the application service — no domain logic in slots
* Inherit from both `QObject` and the corresponding output port interface (e.g., `IScanOutputPort`)
* Register as output port via `service.set_output_port(self)` in `__init__`, not lazily

Full standard is available here for further request: [Presenter Responsibility Boundary](../../../.packmind/standards/presenter-responsibility-boundary.md)