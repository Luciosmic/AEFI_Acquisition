# Application Service Structure

Application services in the `src/application/services/` layer orchestrate hardware ports, domain aggregates, and infrastructure adapters. They must never perform direct IO, never import infrastructure adapters, and must receive all dependencies via constructor injection.

Evidence: `src/application/services/scan_application_service/scan_application_service.py`, `src/application/services/hardware_configuration_service/hardware_configuration_service.py`, `src/application/services/motion_control_service/motion_control_service.py`

## Scope

Python files under `src/application/services/` matching `*_service.py`.

## Rules

* Receive all ports and adapters via `__init__` constructor — never instantiate infrastructure classes directly
* Depend only on port interfaces (`I*.py`) defined in the same service folder or in `domain/`
* Never import from `infrastructure/` directly
* Expose commands (state-mutating methods) and queries (read-only) as distinct method groups
* Publish domain events to `IDomainEventBus` after aggregate state changes — never call output ports directly in command methods
* Each service folder must include at least one port interface file (`i_*.py`) and a `tests/` subfolder
