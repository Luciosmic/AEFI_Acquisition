"""
Test Arcus Lifecycle Initialization with diagram-friendly tracing.

This test verifies that the ArcusPerformaxLifecycleAdapter can successfully
initialize the hardware at software startup, following the pattern used in main.py.

Usage:
    python -m src.infrastructure.hardware.arcus_performax_4EX.tests.test_lifecycle_initialization
"""

import sys
import unittest
from pathlib import Path

# Add src directory to path
# Path structure: .../src/infrastructure/hardware/arcus_performax_4EX/tests/test_lifecycle_initialization.py
# parents[0] = tests/, [1] = arcus_performax_4EX/, [2] = hardware/, [3] = infrastructure/, [4] = src/
src_dir = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(src_dir))

# Import DiagramFriendlyTest from skill
skill_path = Path(__file__).resolve().parents[5] / ".cursor" / "skills" / "diagram_friendly_test"
sys.path.insert(0, str(skill_path))

from diagram_friendly_test import DiagramFriendlyTest

from infrastructure.hardware.arcus_performax_4EX.adapter_motion_port_arcus_performax4EX import ArcusAdapter
from infrastructure.hardware.arcus_performax_4EX.adapter_lifecycle_arcus_performax4EX import ArcusPerformaxLifecycleAdapter


class TestArcusLifecycleInitialization(DiagramFriendlyTest):
    """
    Test the Arcus hardware initialization lifecycle.
    
    This test simulates the initialization sequence used in main.py:
    1. Create ArcusAdapter (disconnected)
    2. Wrap it in ArcusPerformaxLifecycleAdapter
    3. Call initialize_all() to connect
    4. Call verify_all() to verify connection
    5. Call close_all() to cleanup
    """
    
    def setUp(self):
        """Setup test environment."""
        super().setUp()
        
        # Find DLL path (relative to adapter file)
        adapter_dir = Path(__file__).parent.parent
        self.dll_path = adapter_dir / "DLL64"
        
        # Port detection (None = auto-detect)
        self.port = None
        
    def test_lifecycle_initialization(self):
        """
        Test complete lifecycle: initialization, verification, cleanup.
        
        This test follows the exact pattern used in main.py for hardware startup.
        """
        # ============================================================
        # Setup Phase
        # ============================================================
        self.log_divider("Setup Phase")
        
        # Create ArcusAdapter (disconnected state, as in main.py)
        self.log_interaction(
            actor="TestLifecycle",
            action="CREATE",
            target="ArcusAdapter",
            message="Create ArcusAdapter instance (disconnected)",
            data={
                "port": self.port if self.port else "auto-detect",
                "dll_path": str(self.dll_path)
            }
        )
        adapter = ArcusAdapter(port=self.port, dll_path=str(self.dll_path))
        
        # Create Lifecycle Adapter (wraps the adapter)
        self.log_interaction(
            actor="TestLifecycle",
            action="CREATE",
            target="ArcusPerformaxLifecycleAdapter",
            message="Create lifecycle adapter wrapping ArcusAdapter",
            data={"adapter_type": "ArcusAdapter"}
        )
        lifecycle_adapter = ArcusPerformaxLifecycleAdapter(adapter)
        
        # ============================================================
        # Execution Phase - Initialize
        # ============================================================
        self.log_divider("Execution Phase - Initialize")
        
        # Call initialize_all() (as SystemStartupApplicationService would)
        self.log_interaction(
            actor="TestLifecycle",
            action="CALL",
            target="ArcusPerformaxLifecycleAdapter",
            message="initialize_all() - Connect to hardware",
            data={}
        )
        
        try:
            lifecycle_adapter.initialize_all()
            
            # Log successful connection
            self.log_interaction(
                actor="ArcusPerformaxLifecycleAdapter",
                action="RETURN",
                target="TestLifecycle",
                message="initialize_all() completed successfully",
                data={"status": "connected"}
            )
            
        except RuntimeError as e:
            # Log connection failure
            self.log_interaction(
                actor="ArcusPerformaxLifecycleAdapter",
                action="ERROR",
                target="TestLifecycle",
                message="initialize_all() failed",
                data={"error": str(e)}
            )
            raise
        
        # ============================================================
        # Execution Phase - Verify
        # ============================================================
        self.log_divider("Execution Phase - Verify")
        
        # Call verify_all() (as SystemStartupApplicationService would)
        self.log_interaction(
            actor="TestLifecycle",
            action="CALL",
            target="ArcusPerformaxLifecycleAdapter",
            message="verify_all() - Verify hardware connection",
            data={}
        )
        
        try:
            lifecycle_adapter.verify_all()
            
            # Log successful verification
            self.log_interaction(
                actor="ArcusPerformaxLifecycleAdapter",
                action="RETURN",
                target="TestLifecycle",
                message="verify_all() completed successfully",
                data={"status": "verified"}
            )
            
        except RuntimeError as e:
            # Log verification failure
            self.log_interaction(
                actor="ArcusPerformaxLifecycleAdapter",
                action="ERROR",
                target="TestLifecycle",
                message="verify_all() failed",
                data={"error": str(e)}
            )
            raise
        
        # ============================================================
        # Verification Phase - Assertions
        # ============================================================
        self.log_divider("Verification Phase")
        
        # Verify adapter is connected by checking if we can get position
        self.log_interaction(
            actor="TestLifecycle",
            action="CALL",
            target="ArcusAdapter",
            message="get_current_position() - Verify connection works",
            data={}
        )
        
        try:
            position = adapter.get_current_position()
            
            self.log_interaction(
                actor="ArcusAdapter",
                action="RETURN",
                target="TestLifecycle",
                message="Position retrieved successfully",
                data={"x": position.x, "y": position.y}
            )
            
            # Assert position is valid (not None, numeric)
            self.log_interaction(
                actor="TestLifecycle",
                action="ASSERT",
                target="ArcusAdapter",
                message="Position X is numeric",
                expect="numeric value",
                got=f"{position.x} (type: {type(position.x).__name__})"
            )
            self.assertIsInstance(position.x, (int, float))
            
            self.log_interaction(
                actor="TestLifecycle",
                action="ASSERT",
                target="ArcusAdapter",
                message="Position Y is numeric",
                expect="numeric value",
                got=f"{position.y} (type: {type(position.y).__name__})"
            )
            self.assertIsInstance(position.y, (int, float))
            
        except Exception as e:
            self.log_interaction(
                actor="ArcusAdapter",
                action="ERROR",
                target="TestLifecycle",
                message="Failed to get position",
                data={"error": str(e)}
            )
            raise
        
        # ============================================================
        # Cleanup Phase
        # ============================================================
        self.log_divider("Cleanup Phase")
        
        # Call close_all() (as SystemShutdownApplicationService would)
        self.log_interaction(
            actor="TestLifecycle",
            action="CALL",
            target="ArcusPerformaxLifecycleAdapter",
            message="close_all() - Disconnect hardware",
            data={}
        )
        
        try:
            lifecycle_adapter.close_all()
            
            self.log_interaction(
                actor="ArcusPerformaxLifecycleAdapter",
                action="RETURN",
                target="TestLifecycle",
                message="close_all() completed successfully",
                data={"status": "disconnected"}
            )
            
        except Exception as e:
            self.log_interaction(
                actor="ArcusPerformaxLifecycleAdapter",
                action="ERROR",
                target="TestLifecycle",
                message="close_all() failed",
                data={"error": str(e)}
            )
            # Don't raise - cleanup errors are logged but don't fail the test


if __name__ == "__main__":
    unittest.main()

