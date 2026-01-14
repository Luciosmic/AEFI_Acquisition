"""
Integration Test: Scan Export with Event Bus (Diagram-Friendly)

Responsibility:
    Verify the end-to-end flow:
    Scan Execution -> Event Emission -> Handler -> Repository -> HDF5 Persistence.
"""
import shutil
from pathlib import Path
import sys
import os

# Ensure src is in path
sys.path.append(str(Path(__file__).parents[4] / "src"))

from infrastructure.tests.diagram_friendly_test import DiagramFriendlyTest
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.persistence.hdf5_acquisition_repository import HDF5AcquisitionRepository
from application.handlers.acquisition_data_handler import AcquisitionDataHandler
from src.application.services.scan_application_service.scan_application_service import ScanApplicationService
from application.dtos.scan_dtos import Scan2DConfigDTO
from infrastructure.tests.mock_ports import MockMotionPort, MockAcquisitionPort

class ScanExportWithEventBusIntegrationTest(DiagramFriendlyTest):
    
    def setUp(self):
        super().setUp()
        
        # 1. Setup Infrastructure (Persistence)
        # Save HDF5 files in the same directory as the test/results
        self.test_dir = Path(__file__).parent
        
        # Clean up previous HDF5 files to ensure fresh run
        for f in self.test_dir.glob("scan_*.h5"):
            try:
                os.remove(f)
            except OSError:
                pass
            
        # Log relative path for clarity
        try:
            rel_path = f"tests/{self.test_dir.name}"
        except:
            rel_path = str(self.test_dir)

        self.log_interaction("Test", "CREATE", "HDF5Repository", f"Init at {rel_path}", {"path": str(self.test_dir)})
        self.repository = HDF5AcquisitionRepository(base_path=str(self.test_dir))
        
        # 2. Setup Infrastructure (Event Bus)
        self.log_interaction("Test", "CREATE", "EventBus", "Init InMemoryEventBus")
        self.event_bus = InMemoryEventBus()
        
        # 3. Setup Application (Handler)
        self.log_interaction("Test", "CREATE", "AcquisitionHandler", "Init with Repository")
        self.handler = AcquisitionDataHandler(self.repository)
        
        # 4. Wire Handler to Event Bus
        self.log_interaction("Test", "SUBSCRIBE", "EventBus", "Handler subscribes to scanpointacquired")
        self.event_bus.subscribe("scanpointacquired", self.handler.handle)
        
        # 5. Setup Application (Service)
        self.log_interaction("Test", "CREATE", "ScanService", "Init with Ports & Bus")
        self.motion_port = MockMotionPort()
        self.acquisition_port = MockAcquisitionPort()
        self.scan_service = ScanApplicationService(
            self.motion_port, 
            self.acquisition_port, 
            self.event_bus
        )

    def tearDown(self):
        super().tearDown()
        # Do not delete the HDF5 file so the user can inspect it
        pass

    def test_scan_export_flow(self):
        """
        Execute a scan and verify data is persisted via events.
        """
        self.log_interaction("Test", "START", "ScanService", "Start Integration Test")
        
        # 1. Configure Scan
        config = Scan2DConfigDTO(
            x_min=0, x_max=1, x_nb_points=2,
            y_min=0, y_max=1, y_nb_points=2,
            scan_pattern="RASTER",
            stabilization_delay_ms=0,
            averaging_per_position=1,
            uncertainty_volts=1e-6
        )
        self.log_interaction("Test", "COMMAND", "ScanService", "Execute Scan", {"pattern": "RASTER", "grid": "2x2"})
        
        # 2. Execute Scan
        # This will trigger:
        # Service -> EventBus (ScanStarted)
        # Service -> Motion -> Acquisition
        # Service -> EventBus (ScanPointAcquired) -> Handler -> Repository -> HDF5
        # Service -> EventBus (ScanCompleted)
        success = self.scan_service.execute_scan(config)
        
        self.log_interaction("Test", "ASSERT", "ScanService", "Check execution success", expect=True, got=success)
        self.assertTrue(success)
        
        # 3. Verify Persistence
        # We expect 4 points (2x2)
        scan_id = str(self.scan_service.current_scan_id) if hasattr(self.scan_service, 'current_scan_id') else "unknown"
        # Since we don't easily know the scan_id generated inside the service unless exposed,
        # we might need to find the file or capture the ID from events if we were listening.
        # For this test, let's look at the file system or assume the service exposes it.
        # Actually, ScanApplicationService doesn't expose current_scan_id publicly easily.
        # But HDF5Repository stores files as scan_{id}.h5. Let's find the file.
        
        self.log_interaction("Test", "QUERY", "FileSystem", "Find generated HDF5 file")
        files = list(self.test_dir.glob("*.h5"))
        
        self.log_interaction("Test", "ASSERT", "FileSystem", "Check file count", expect=1, got=len(files))
        self.assertEqual(len(files), 1)
        
        if files:
            found_scan_id = files[0].stem.replace("scan_", "")
            self.log_interaction("Test", "QUERY", "HDF5Repository", "Load data from file", {"scan_id": found_scan_id})
            samples = self.repository.find_by_scan(found_scan_id)
            
            self.log_interaction("Test", "ASSERT", "HDF5Repository", "Check sample count", expect=4, got=len(samples))
            self.assertEqual(len(samples), 4)
