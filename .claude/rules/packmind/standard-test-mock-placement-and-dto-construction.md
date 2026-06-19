---
name: 'Test Mock Placement and DTO Construction'
alwaysApply: true
description: 'Standardize Python test mock adapter placement in `src/infrastructure/mocks/` (using `adapter_mock_` file prefixes), event bus usage via `InMemoryEventBus`, and reusable DTO factories `make_<dto_name>(**overrides)` (with concise setup and `DiagramFriendlyTest` for service flows) to reduce duplication and keep tests stable and maintainable.'
---

# Standard: Test Mock Placement and DTO Construction

Standardize Python test mock adapter placement in `src/infrastructure/mocks/` (using `adapter_mock_` file prefixes), event bus usage via `InMemoryEventBus`, and reusable DTO factories `make_<dto_name>(**overrides)` (with concise setup and `DiagramFriendlyTest` for service flows) to reduce duplication and keep tests stable and maintainable. :
* Avoid `setUp` methods that exceed 20 lines — extract to named factory functions
* For DTOs used in multiple tests, create a factory function `make_<dto_name>(**overrides)` in the test folder's `__init__.py`
* Name mock files with the `adapter_mock_` prefix matching the port they implement (e.g., `adapter_mock_i_motion_port.py`)
* Place shared mock adapters in `src/infrastructure/mocks/` — never duplicate mock classes across test files
* Prefer `DiagramFriendlyTest` base class when testing application service flows to preserve interaction diagrams
* Use `InMemoryEventBus` from `src/infrastructure/` for all tests that need an event bus — never create a stub bus in a test file

Full standard is available here for further request: [Test Mock Placement and DTO Construction](../../../.packmind/standards/test-mock-placement-and-dto-construction.md)