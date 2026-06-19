---
name: 'Application Service Structure'
alwaysApply: true
description: 'Enforce Python application service structure under `src/application/services/*_service.py` with constructor-injected port interfaces (`I*.py`/`i_*.py`), no direct IO or `infrastructure/` imports, clear command/query separation, and post-change domain event publication via `IDomainEventBus` to preserve layering, testability, and maintainable orchestration.'
---

# Standard: Application Service Structure

Enforce Python application service structure under `src/application/services/*_service.py` with constructor-injected port interfaces (`I*.py`/`i_*.py`), no direct IO or `infrastructure/` imports, clear command/query separation, and post-change domain event publication via `IDomainEventBus` to preserve layering, testability, and maintainable orchestration. :
* Depend only on port interfaces (`I*.py`) defined in the same service folder or in `domain/`
* Each service folder must include at least one port interface file (`i_*.py`) and a `tests/` subfolder
* Expose commands (state-mutating methods) and queries (read-only) as distinct method groups
* Never import from `infrastructure/` directly
* Publish domain events to `IDomainEventBus` after aggregate state changes — never call output ports directly in command methods
* Receive all ports and adapters via `__init__` constructor — never instantiate infrastructure classes directly

Full standard is available here for further request: [Application Service Structure](../../../.packmind/standards/application-service-structure.md)