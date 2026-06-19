# Port Interface Naming and Placement

Port interfaces define the contract between application services and infrastructure adapters. They follow a strict naming and placement convention derived from Hexagonal Architecture.

Evidence: `src/application/services/scan_application_service/i_acquisition_port.py`, `src/application/services/hardware_configuration_service/i_hardware_advanced_configurator.py`, `src/application/services/motion_control_service/i_motion_port.py`

## Scope

Python files defining abstract port contracts (`ABC` subclasses) across `src/application/` and `src/domain/`.

## Rules

* Name port interface files with the `i_` prefix followed by the role (e.g., `i_motion_port.py`, `i_scan_export_port.py`)
* Place port interfaces in the same folder as the service that consumes them — not in a global `ports/` directory
* Inherit from `ABC` and mark every method with `@abstractmethod`
* Include a docstring block explaining: Responsibility, Rationale, and Design
* Never put implementation logic in port files — ports are pure contracts
* Input ports (service → infrastructure) and output ports (infrastructure → service) must be separate files
