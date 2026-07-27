---
name: 'Test Mock Placement and DTO Construction'
alwaysApply: true
description: 'Test Mock Placement and DTO Construction'
---

# Standard: Test Mock Placement and DTO Construction

Tests across multiple layers use shared mock adapters and construct domain DTOs inline. A consistent strategy for mock placement and DTO construction prevents duplication and brittle tests. :
* Avoid `setUp` methods that exceed 20 lines — extract to named factory functions
* For DTOs used in multiple tests, create a factory function `make_<dto_name>(**overrides)` in the test folder's `__init__.py`
* Name mock files with the `adapter_mock_` prefix matching the port they implement (e.g., `adapter_mock_i_motion_port.py`)
* Place shared mock adapters in `src/infrastructure/mocks/` — never duplicate mock classes across test files
* Prefer `DiagramFriendlyTest` base class when testing application service flows to preserve interaction diagrams
* Use `InMemoryEventBus` from `src/infrastructure/` for all tests that need an event bus — never create a stub bus in a test file

Full standard is available here for further request: [Test Mock Placement and DTO Construction](../../../.packmind/standards/test-mock-placement-and-dto-construction.md)