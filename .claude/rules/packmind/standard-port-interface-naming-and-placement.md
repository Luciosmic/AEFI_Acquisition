---
name: 'Port Interface Naming and Placement'
alwaysApply: true
description: 'Enforce Hexagonal Architecture port interface naming and placement for Python `ABC` contracts under `src/application/` and `src/domain/` (use `i_*.py` beside consuming services, separate input/output ports, `@abstractmethod`-only methods with Responsibility/Rationale/Design docstrings, and no implementation logic) to keep service–adapter boundaries explicit and maintainable.'
---

# Standard: Port Interface Naming and Placement

Enforce Hexagonal Architecture port interface naming and placement for Python `ABC` contracts under `src/application/` and `src/domain/` (use `i_*.py` beside consuming services, separate input/output ports, `@abstractmethod`-only methods with Responsibility/Rationale/Design docstrings, and no implementation logic) to keep service–adapter boundaries explicit and maintainable. :
* Include a docstring block explaining: Responsibility, Rationale, and Design
* Inherit from `ABC` and mark every method with `@abstractmethod`
* Input ports (service → infrastructure) and output ports (infrastructure → service) must be separate files
* Name port interface files with the `i_` prefix followed by the role (e.g., `i_motion_port.py`, `i_scan_export_port.py`)
* Never put implementation logic in port files — ports are pure contracts
* Place port interfaces in the same folder as the service that consumes them — not in a global `ports/` directory

Full standard is available here for further request: [Port Interface Naming and Placement](../../../.packmind/standards/port-interface-naming-and-placement.md)