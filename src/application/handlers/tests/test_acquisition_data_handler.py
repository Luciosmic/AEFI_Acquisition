"""
Tests for AcquisitionDataHandler (Diagram-Friendly)
"""
from unittest.mock import MagicMock
from uuid import uuid4
from datetime import datetime

from application.handlers.acquisition_data_handler import AcquisitionDataHandler
from domain.models.scan.events.scan_events import ScanPointAcquired
from domain.models.aefi_device.value_objects.acquisition.acquisition_sample import AcquisitionSample
from domain.shared.value_objects.position_2d import Position2D
from infrastructure.tests.diagram_friendly_test import DiagramFriendlyTest

class TestAcquisitionDataHandler(DiagramFriendlyTest):
    """Test AcquisitionDataHandler orchestration."""
    
    def setUp(self):
        super().setUp()
        self.mock_repo = MagicMock()
        self.log_interaction("Test", "CREATE", "AcquisitionDataHandler", "Initialize handler with mock repo")
        self.handler = AcquisitionDataHandler(self.mock_repo)
        
    def test_handle_scan_point_acquired(self):
        """Test handling of ScanPointAcquired event."""
        scan_id = uuid4()
        sample = AcquisitionSample(
            timestamp=datetime.now(),
            voltage_x_in_phase=1.0, voltage_x_quadrature=0.0,
            voltage_y_in_phase=0.0, voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0, voltage_z_quadrature=0.0
        )
        
        event = ScanPointAcquired(
            scan_id=scan_id,
            point_index=0,
            position=Position2D(0, 0),
            measurement=sample
        )
        
        self.log_interaction("Test", "PUBLISH", "EventBus", "Simulate ScanPointAcquired event", {"scan_id": str(scan_id)})
        # Simulate the handler receiving the event directly (or via bus if we had one set up)
        self.log_interaction("EventBus", "RECEIVE", "AcquisitionDataHandler", "Handle event")
        self.handler.handle(event)
        
        self.log_interaction("AcquisitionDataHandler", "CALL", "Repository", "Save data", {"scan_id": str(scan_id)})
        
        # Verify repository call
        self.mock_repo.save.assert_called_once()
        args = self.mock_repo.save.call_args
        called_scan_id = args[0][0]
        called_data = args[0][1]
        
        self.log_interaction("Test", "ASSERT", "Repository", "Verify save called with correct scan_id", expect=str(scan_id), got=str(called_scan_id))
        self.assertEqual(called_scan_id, scan_id)
        
        self.log_interaction("Test", "ASSERT", "Repository", "Verify save called with correct data", expect=1, got=len(called_data))
        self.assertEqual(len(called_data), 1)
        self.assertEqual(called_data[0], sample)
