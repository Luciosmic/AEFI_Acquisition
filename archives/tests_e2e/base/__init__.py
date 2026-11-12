"""
Base infrastructure for E2E tests.
"""

from .base_agent_test import DiagramFriendlyTest
# e2e_test_environment import removed to avoid dependency on hardware_parameter_dtos
# Import it directly if needed: from tests_e2e.base.e2e_test_environment import TestEnvironment, TestContext
# fixtures_test import commented out - import directly if needed to avoid dependency issues
# from .fixtures_test import (
#     create_scan_config,
#     create_mock_motion_port,
#     create_mock_acquisition_port,
#     create_event_bus,
#     create_step_scan,
#     create_motion_profile_selector,
#     create_simple_trajectory,
# )

__all__ = [
    "DiagramFriendlyTest",
    # "TestEnvironment",  # Commented out - import directly if needed
    # "TestContext",       # Commented out - import directly if needed
    # "create_scan_config",  # Import from fixtures_test directly if needed
    # "create_mock_motion_port",
    # "create_mock_acquisition_port",
    # "create_event_bus",
    # "create_step_scan",
    # "create_motion_profile_selector",
    # "create_simple_trajectory",
]

