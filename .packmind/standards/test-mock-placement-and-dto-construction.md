# Test Mock Placement and DTO Construction

Tests across multiple layers use shared mock adapters and construct domain DTOs inline. A consistent strategy for mock placement and DTO construction prevents duplication and brittle tests.

Evidence: `src/application/services/scan_application_service/tests/scan_application_service_test.py:5-6` (imports `MockMotionPort`, `MockAcquisitionPort` from infrastructure), `src/infrastructure/mocks/adapter_mock_i_motion_port.py`, `src/infrastructure/mocks/adapter_mock_scan_executor.py`

## Scope

Python test files under `src/` matching `*_test.py` or `test_*.py`.

## Rules

* Place shared mock adapters in `src/infrastructure/mocks/` — never duplicate mock classes across test files
* Name mock files with the `adapter_mock_` prefix matching the port they implement (e.g., `adapter_mock_i_motion_port.py`)
* Use `InMemoryEventBus` from `src/infrastructure/` for all tests that need an event bus — never create a stub bus in a test file
* For DTOs used in multiple tests, create a factory function `make_<dto_name>(**overrides)` in the test folder's `__init__.py`
* Avoid `setUp` methods that exceed 20 lines — extract to named factory functions
* Prefer `DiagramFriendlyTest` base class when testing application service flows to preserve interaction diagrams
