import unittest
import time
import sys
from pathlib import Path

from tool.diagram_friendly_test import DiagramFriendlyTest
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from application.services.continuous_acquisition_service.continuous_acquisition_service import ContinuousAcquisitionService
from application.services.continuous_acquisition_service.i_continuous_acquisition_executor import ContinuousAcquisitionConfig
from src.application.services.scan_application_service.ports.i_acquisition_port import IAcquisitionPort
from domain.models.aefi_device.value_objects.acquisition.voltage_measurement import VoltageMeasurement
from datetime import datetime
import random

from infrastructure.hardware.micro_controller.ads131a04.adapter_i_continuous_acquisition_ads131a04 import AdapterIContinuousAcquisitionAds131a04

# Ensure src is in path
# Ensure src is in path
src_path = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

class RandomNoiseAcquisitionPort(IAcquisitionPort):
    def acquire_sample(self) -> VoltageMeasurement:
        return VoltageMeasurement(
            voltage_x_in_phase=random.uniform(-1, 1),
            voltage_x_quadrature=random.uniform(-1, 1),
            voltage_y_in_phase=random.uniform(-1, 1),
            voltage_y_quadrature=random.uniform(-1, 1),
            voltage_z_in_phase=random.uniform(-1, 1),
            voltage_z_quadrature=random.uniform(-1, 1),
            timestamp=datetime.now(),
            uncertainty_estimate_volts=0.01
        )
    
    def is_ready(self) -> bool:
        return True

class TestContinuousAcquisitionSequence(DiagramFriendlyTest):
    def test_full_acquisition_cycle(self):
        # 1. Setup / Composition Root
        self.log_interaction("Test", "CREATE", "EventBus", "Initialize EventBus")
        event_bus = InMemoryEventBus()

        self.log_interaction("Test", "CREATE", "AcquisitionPort", "Initialize Mock Port")
        mock_port = RandomNoiseAcquisitionPort()

        self.log_interaction("Test", "CREATE", "AdapterIContinuousAcquisitionAds131a04", "Initialize Adapter")
        executor = AdapterIContinuousAcquisitionAds131a04(event_bus)

        self.log_interaction("Test", "CREATE", "Service", "Initialize Service", 
                             data={"dependency": "AdapterIContinuousAcquisitionAds131a04", "port": "AcquisitionPort"})
        service = ContinuousAcquisitionService(executor, mock_port)

        # 2. Subscribe to events to verify flow
        received_samples = []
        def on_sample(event):
            self.log_interaction("EventBus", "RECEIVE", "TestSubscriber", "Sample Acquired", 
                                 data={"index": event.sample_index})
            received_samples.append(event)

        self.log_interaction("TestSubscriber", "SUBSCRIBE", "EventBus", "continuousacquisitionsampleacquired")
        event_bus.subscribe("continuousacquisitionsampleacquired", on_sample)

        # 3. Start Acquisition
        config = ContinuousAcquisitionConfig(sample_rate_hz=10.0)
        self.log_interaction("Test", "COMMAND", "Service", "start_acquisition", 
                             data={"rate": 10.0})
        service.start_acquisition(config)

        # 4. Wait for execution (simulating runtime)
        time.sleep(0.5)

        # 5. Stop Acquisition
        self.log_interaction("Test", "COMMAND", "Service", "stop_acquisition")
        service.stop_acquisition()

        # 6. Assertions
        self.log_interaction("Test", "ASSERT", "TestSubscriber", "Verify samples received", 
                             expect="> 0 samples", got=f"{len(received_samples)} samples")
        self.assertTrue(len(received_samples) > 0)

if __name__ == '__main__':
    unittest.main()
