---
name: 'Port Interface Naming and Placement'
alwaysApply: true
description: 'Port Interface Naming and Placement'
---

# Standard: Port Interface Naming and Placement

Port interfaces define the contract between application services and infrastructure adapters. They follow a strict naming and placement convention derived from Hexagonal Architecture. :
* Include a docstring block explaining: Responsibility, Rationale, and Design
* Inherit from `ABC` and mark every method with `@abstractmethod`
* Input ports (service → infrastructure) and output ports (infrastructure → service) must be separate files
* Name port interface files with the `i_` prefix followed by the role (e.g., `i_motion_port.py`, `i_scan_export_port.py`)
* Never put implementation logic in port files — ports are pure contracts
* Place port interfaces in the same folder as the service that consumes them — not in a global `ports/` directory

Full standard is available here for further request: [Port Interface Naming and Placement](../../../.packmind/standards/port-interface-naming-and-placement.md)