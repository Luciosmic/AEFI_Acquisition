import sys
import os
import unittest
from datetime import datetime

# Add src to path
# Current path: src/infrastructure/hardware/micro_controller/ads131a04/tests/
# Need to go up 5 levels to reach src parent, then import from src or add src to path
# .. -> ads131a04
# ../.. -> micro_controller
# ../../.. -> hardware
# ../../../.. -> infrastructure
# ../../../../.. -> src
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../..'))

from tool.diagram_friendly_test import DiagramFriendlyTest
from infrastructure.hardware.micro_controller.adapter_lifecycle_MCU import MCULifecycleAdapter
from infrastructure.hardware.micro_controller.ads131a04.adapter_i_acquistion_port_ads131a04 import ADS131A04Adapter
from domain.value_objects.measurement_uncertainty import MeasurementUncertainty

class TestAcquisitionSequence(DiagramFriendlyTest):
    
    def test_full_acquisition_flow(self):
        # --- Setup Phase ---
        self.log_divider("Setup Phase")
        
        # 1. Initialize MCU Lifecycle
        self.log_interaction(
            actor="TestAcquisition",
            action="CREATE",
            target="MCULifecycleAdapter",
            message="Initialize MCU Lifecycle Adapter",
            data={"port": "COM10", "baudrate": 1500000}
        )
        mcu_lifecycle = MCULifecycleAdapter(port="COM10", baudrate=1500000)
        
        # 2. Connect to Hardware
        self.log_interaction(
            actor="MCULifecycleAdapter",
            action="CALL",
            target="MCU_SerialCommunicator",
            message="connect",
            data={"port": "COM10"}
        )
        mcu_lifecycle.initialize_all()
        
        # 3. Initialize Acquisition Adapter
        self.log_interaction(
            actor="TestAcquisition",
            action="CREATE",
            target="ADS131A04Adapter",
            message="Initialize Acquisition Adapter"
        )
        communicator = mcu_lifecycle.get_communicator()
        adapter = ADS131A04Adapter(communicator)
        
        # --- Execution Phase ---
        self.log_divider("Execution Phase")
        
        # 4. Configure Adapter
        self.log_interaction(
            actor="TestAcquisition",
            action="CALL",
            target="ADS131A04Adapter",
            message="configure_for_uncertainty",
            data={"max_uncertainty": 0.001}
        )
        uncertainty = MeasurementUncertainty(max_uncertainty_volts=0.001)
        adapter.configure_for_uncertainty(uncertainty)
        
        # 5. Acquire Sample
        self.log_interaction(
            actor="TestAcquisition",
            action="CALL",
            target="ADS131A04Adapter",
            message="acquire_sample"
        )
        
        # Simulating internal interaction for the diagram
        self.log_interaction(
            actor="ADS131A04Adapter",
            action="CALL",
            target="MCU_SerialCommunicator",
            message="send_command('m1')"
        )
        
        measurement = adapter.acquire_sample()
        
        self.log_interaction(
            actor="ADS131A04Adapter",
            action="RETURN",
            target="TestAcquisition",
            message="VoltageMeasurement",
            data={
                "ch1": f"{measurement.voltage_x_in_phase:.6f}",
                "timestamp": measurement.timestamp.isoformat()
            }
        )
        
        # --- Verification Phase ---
        self.log_divider("Verification Phase")
        
        # 6. Assertions
        self.log_interaction(
            actor="TestAcquisition",
            action="ASSERT",
            target="Measurement",
            message="Verify measurement is not None",
            expect="VoltageMeasurement object",
            got="VoltageMeasurement object"
        )
        self.assertIsNotNone(measurement)
        
        # Cleanup
        self.log_interaction(
            actor="TestAcquisition",
            action="CALL",
            target="MCULifecycleAdapter",
            message="close_all"
        )
        mcu_lifecycle.close_all()

if __name__ == '__main__':
    unittest.main()
