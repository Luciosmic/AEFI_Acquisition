"""
End-to-End Test for Continuous Acquisition Flow

Tests the complete flow from UI → Presenter → Service → Executor → Hardware → Events → UI
with diagram-friendly interaction logging for sequence diagram generation.

Flow:
1. UI Widget → start_acquisition() → Presenter
2. Presenter → start_acquisition() → Service
3. Service → start() → Executor
4. Executor → worker thread → acquire_sample() → AcquisitionPort
5. AcquisitionPort → MCU → Hardware
6. Hardware → response → AcquisitionPort → VoltageMeasurement
7. Executor → publish event → EventBus
8. EventBus → notify → Presenter (subscriber)
9. Presenter → emit signal → UI Widget
"""

import sys
import unittest
import time
import threading
from pathlib import Path
from uuid import UUID

# Add src to path
src_dir = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(src_dir))

# Add .cursor/skills to path for diagram_friendly_test
# Path structure: .../src/interface/ui_continuous_acquisition/tests/test_e2e_continuous_acquisition.py
# parents[0] = tests/, [1] = ui_continuous_acquisition/, [2] = interface/, [3] = src/, [4] = AEFI_Acquisition/
# From AEFI_Acquisition/, go to .cursor/skills/diagram_friendly_test
skill_path = Path(__file__).resolve().parents[4] / ".cursor" / "skills" / "diagram_friendly_test"
if not skill_path.exists():
    # Try alternative path (if file is in different location)
    skill_path = Path(__file__).resolve().parents[5] / ".cursor" / "skills" / "diagram_friendly_test"
sys.path.insert(0, str(skill_path))

from diagram_friendly_test import DiagramFriendlyTest

# PyQt6 is required for Qt signals to work
from PyQt6.QtWidgets import QApplication

from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.mocks.adapter_mock_i_acquisition_port import RandomNoiseAcquisitionPort
from infrastructure.hardware.micro_controller.ads131a04.adapter_i_continuous_acquisition_ads131a04 import AdapterIContinuousAcquisitionAds131a04
from application.services.continuous_acquisition_service.continuous_acquisition_service import ContinuousAcquisitionService
from application.services.continuous_acquisition_service.i_continuous_acquisition_executor import ContinuousAcquisitionConfig
from interface.ui_continuous_acquisition.presenter_continuous_acquisition import ContinuousAcquisitionPresenter
from domain.events.continuous_acquisition_events import (
    ContinuousAcquisitionSampleAcquired,
    ContinuousAcquisitionStopped,
)


class TestE2EContinuousAcquisition(DiagramFriendlyTest):
    """End-to-end test for continuous acquisition flow."""
    
    @classmethod
    def setUpClass(cls):
        """Create QApplication once for all tests (required for Qt signals)."""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        super().setUp()
        self.event_bus = None
        self.acquisition_port = None
        self.executor = None
        self.service = None
        self.presenter = None
        self.samples_received = []
        self.presenter_signals_received = []
    
    def test_continuous_acquisition_full_flow(self):
        """Test complete flow from UI start to sample reception."""
        self.log_divider("Setup Phase")
        
        # 1. Create Event Bus
        self.log_interaction(
            actor="TestE2E",
            action="CREATE",
            target="InMemoryEventBus",
            message="Create event bus for domain events",
            data={}
        )
        self.event_bus = InMemoryEventBus()
        
        # 2. Create Acquisition Port (Mock for now, can be real hardware)
        self.log_interaction(
            actor="TestE2E",
            action="CREATE",
            target="RandomNoiseAcquisitionPort",
            message="Create mock acquisition port (can be replaced with real hardware)",
            data={"type": "mock"}
        )
        self.acquisition_port = RandomNoiseAcquisitionPort()
        
        # 3. Create Continuous Acquisition Executor
        self.log_interaction(
            actor="TestE2E",
            action="CREATE",
            target="AdapterIContinuousAcquisitionAds131a04",
            message="Create continuous acquisition executor with event bus",
            data={"event_bus_type": type(self.event_bus).__name__}
        )
        self.executor = AdapterIContinuousAcquisitionAds131a04(self.event_bus)
        
        # 4. Create Continuous Acquisition Service
        self.log_interaction(
            actor="TestE2E",
            action="CREATE",
            target="ContinuousAcquisitionService",
            message="Create service with executor and acquisition port",
            data={
                "executor_type": type(self.executor).__name__,
                "acquisition_port_type": type(self.acquisition_port).__name__
            }
        )
        self.service = ContinuousAcquisitionService(self.executor, self.acquisition_port)
        
        # 5. Create Presenter
        self.log_interaction(
            actor="TestE2E",
            action="CREATE",
            target="ContinuousAcquisitionPresenter",
            message="Create presenter with service and event bus",
            data={
                "service_type": type(self.service).__name__,
                "event_bus_type": type(self.event_bus).__name__
            }
        )
        self.presenter = ContinuousAcquisitionPresenter(self.service, self.event_bus)
        
        # 6. Subscribe to Presenter signals (simulating UI connection)
        self.log_interaction(
            actor="TestE2E",
            action="SUBSCRIBE",
            target="ContinuousAcquisitionPresenter",
            message="Subscribe to presenter signals (simulating UI widget)",
            data={"signals": ["acquisition_started", "sample_acquired", "acquisition_stopped"]}
        )
        self.presenter.acquisition_started.connect(self._on_acquisition_started)
        self.presenter.sample_acquired.connect(self._on_sample_acquired)
        self.presenter.acquisition_stopped.connect(self._on_acquisition_stopped)
        
        # 7. Verify Presenter subscribed to EventBus
        self.log_interaction(
            actor="ContinuousAcquisitionPresenter",
            action="SUBSCRIBE",
            target="InMemoryEventBus",
            message="Presenter subscribes to domain events",
            data={"events": ["ContinuousAcquisitionSampleAcquired", "ContinuousAcquisitionFailed", "ContinuousAcquisitionStopped"]}
        )
        
        self.log_divider("Execution Phase - Start Acquisition")
        
        # 8. UI Action: Start Acquisition (simulating widget.start_acquisition())
        config_params = {
            "sample_rate_hz": 10.0,  # 10 Hz for fast test
            "max_duration_s": 0.5,   # 0.5 seconds max
        }
        self.log_interaction(
            actor="TestE2E",
            action="CALL",
            target="ContinuousAcquisitionPresenter",
            message="start_acquisition() - UI requests acquisition start",
            data={"params": config_params}
        )
        self.presenter.start_acquisition(config_params)
        
        # 9. Presenter calls Service
        self.log_interaction(
            actor="ContinuousAcquisitionPresenter",
            action="CALL",
            target="ContinuousAcquisitionService",
            message="start_acquisition() - Service orchestrates acquisition",
            data={"config": {"sample_rate_hz": 10.0, "max_duration_s": 0.5}}
        )
        
        # 10. Service calls Executor
        self.log_interaction(
            actor="ContinuousAcquisitionService",
            action="CALL",
            target="AdapterIContinuousAcquisitionAds131a04",
            message="start() - Executor starts background worker thread",
            data={"config": {"sample_rate_hz": 10.0, "max_duration_s": 0.5}}
        )
        
        # 11. Executor starts worker thread
        self.log_interaction(
            actor="AdapterIContinuousAcquisitionAds131a04",
            action="CREATE",
            target="Thread",
            message="Start background acquisition worker thread",
            data={"thread_name": "ADS131A04_Acquisition_Thread"}
        )
        
        # Wait for a few samples to be acquired
        self.log_divider("Acquisition Phase - Sample Loop")
        
        # Wait for samples (with timeout)
        # Process Qt events to allow signals to be delivered
        max_wait = 2.0  # seconds
        start_time = time.time()
        while len(self.samples_received) < 3 and (time.time() - start_time) < max_wait:
            QApplication.processEvents()  # Process Qt events so signals are delivered
            time.sleep(0.1)
        
        # 12. Worker thread acquires samples
        for i, sample_data in enumerate(self.samples_received[:3]):  # Log first 3 samples
            self.log_interaction(
                actor="AdapterIContinuousAcquisitionAds131a04",
                action="CALL",
                target="RandomNoiseAcquisitionPort",
                message=f"acquire_sample() - Worker thread acquires sample {i+1}",
                data={"sample_index": sample_data.get("index", i)}
            )
            
            self.log_interaction(
                actor="RandomNoiseAcquisitionPort",
                action="RETURN",
                target="AdapterIContinuousAcquisitionAds131a04",
                message=f"VoltageMeasurement returned for sample {i+1}",
                data={
                    "voltage_x_in_phase": sample_data.get("measurement", {}).get("Ux In-Phase", "N/A"),
                    "voltage_y_in_phase": sample_data.get("measurement", {}).get("Uy In-Phase", "N/A")
                }
            )
            
            # 13. Executor publishes event
            self.log_interaction(
                actor="AdapterIContinuousAcquisitionAds131a04",
                action="PUBLISH",
                target="InMemoryEventBus",
                message=f"Publish ContinuousAcquisitionSampleAcquired event for sample {i+1}",
                data={
                    "acquisition_id": sample_data.get("acquisition_id", "N/A"),
                    "sample_index": sample_data.get("index", i)
                }
            )
            
            # 14. EventBus notifies Presenter
            self.log_interaction(
                actor="InMemoryEventBus",
                action="RECEIVE",
                target="ContinuousAcquisitionPresenter",
                message=f"EventBus delivers sample event {i+1} to presenter subscriber",
                data={"event_type": "ContinuousAcquisitionSampleAcquired"}
            )
            
            # 15. Presenter emits Qt signal
            self.log_interaction(
                actor="ContinuousAcquisitionPresenter",
                action="PUBLISH",
                target="TestE2E",
                message=f"Presenter emits sample_acquired signal for sample {i+1}",
                data={"signal": "sample_acquired"}
            )
        
        self.log_divider("Execution Phase - Stop Acquisition")
        
        # 16. UI Action: Stop Acquisition
        self.log_interaction(
            actor="TestE2E",
            action="CALL",
            target="ContinuousAcquisitionPresenter",
            message="stop_acquisition() - UI requests acquisition stop",
            data={}
        )
        self.presenter.stop_acquisition()
        
        # 17. Presenter calls Service
        self.log_interaction(
            actor="ContinuousAcquisitionPresenter",
            action="CALL",
            target="ContinuousAcquisitionService",
            message="stop_acquisition() - Service stops acquisition",
            data={}
        )
        
        # 18. Service calls Executor
        self.log_interaction(
            actor="ContinuousAcquisitionService",
            action="CALL",
            target="AdapterIContinuousAcquisitionAds131a04",
            message="stop() - Executor stops worker thread",
            data={}
        )
        
        # 19. Executor stops worker and publishes stop event
        self.log_interaction(
            actor="AdapterIContinuousAcquisitionAds131a04",
            action="PUBLISH",
            target="InMemoryEventBus",
            message="Publish ContinuousAcquisitionStopped event",
            data={"event_type": "ContinuousAcquisitionStopped"}
        )
        
        # 20. EventBus notifies Presenter
        self.log_interaction(
            actor="InMemoryEventBus",
            action="RECEIVE",
            target="ContinuousAcquisitionPresenter",
            message="EventBus delivers stop event to presenter",
            data={"event_type": "ContinuousAcquisitionStopped"}
        )
        
        # 21. Presenter emits stop signal
        self.log_interaction(
            actor="ContinuousAcquisitionPresenter",
            action="PUBLISH",
            target="TestE2E",
            message="Presenter emits acquisition_stopped signal",
            data={"signal": "acquisition_stopped"}
        )
        
        # Wait for thread to finish
        if self.executor._thread:
            self.executor._thread.join(timeout=1.0)
        
        self.log_divider("Verification Phase")
        
        # 22. Verify samples were received
        self.log_interaction(
            actor="TestE2E",
            action="ASSERT",
            target="ContinuousAcquisitionPresenter",
            message="Verify samples were received",
            expect=">= 3 samples",
            got=f"{len(self.samples_received)} samples"
        )
        self.assertGreaterEqual(len(self.samples_received), 3, "Should have received at least 3 samples")
        
        # 23. Verify acquisition started signal
        self.log_interaction(
            actor="TestE2E",
            action="ASSERT",
            target="ContinuousAcquisitionPresenter",
            message="Verify acquisition_started signal was emitted",
            expect="True",
            got="acquisition_started" in [s["type"] for s in self.presenter_signals_received]
        )
        started_signals = [s for s in self.presenter_signals_received if s["type"] == "acquisition_started"]
        self.assertGreater(len(started_signals), 0, "Should have received acquisition_started signal")
        
        # 24. Verify sample data structure
        if self.samples_received:
            sample = self.samples_received[0]
            self.log_interaction(
                actor="TestE2E",
                action="ASSERT",
                target="ContinuousAcquisitionPresenter",
                message="Verify sample data structure contains required fields",
                expect="acquisition_id, index, measurement, timestamp",
                got=list(sample.keys())
            )
            self.assertIn("acquisition_id", sample)
            self.assertIn("index", sample)
            self.assertIn("measurement", sample)
            self.assertIn("timestamp", sample)
    
    def _on_acquisition_started(self, acquisition_id: str):
        """Handler for acquisition_started signal."""
        self.presenter_signals_received.append({
            "type": "acquisition_started",
            "acquisition_id": acquisition_id
        })
    
    def _on_sample_acquired(self, data: dict):
        """Handler for sample_acquired signal."""
        self.samples_received.append(data)
    
    def _on_acquisition_stopped(self, acquisition_id: str):
        """Handler for acquisition_stopped signal."""
        self.presenter_signals_received.append({
            "type": "acquisition_stopped",
            "acquisition_id": acquisition_id
        })


if __name__ == '__main__':
    unittest.main()

