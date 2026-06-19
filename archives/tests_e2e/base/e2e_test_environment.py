import sys
import threading
import time
from dataclasses import dataclass
from typing import Optional
from unittest.mock import MagicMock

# Ensure src is in path for relative imports if run as script
import os
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from PyQt6.QtWidgets import QApplication

# Core Services
from application.services.scan_application_service.scan_application_service import ScanApplicationService
from application.services.hardware_configuration_service.hardware_configuration_service import HardwareConfigurationService
from infrastructure.real.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.real.execution.step_scan_executor import StepScanExecutor

# Ports & Adapters
# CORRECTED IMPORTS
from infrastructure.fake.hardware.arcus_performax_4EX.fake_motion_port import FakeMotionPort
from infrastructure.fake.hardware.micro_controller.ads131a04.fake_acquisition_port import FakeAcquisitionPort
from infrastructure.fake.hardware.fake_hardware_config_provider import FakeHardwareConfigProvider
from infrastructure.fake.hardware.fake_hardware_initialization_port import FakeHardwareInitializationPort

# UI
from interface.ui_2d_scan.presenter_2d_scan import ScanPresenter
from interface.ui_excitation_configuration.presenter_excitation import ExcitationPresenter
from interface.ui_continuous_acquisition.presenter_continuous_acquisition import ContinuousAcquisitionPresenter
from presentation.shell.main_window import MainWindow

@dataclass
class TestContext:
    app: QApplication
    main_window: MainWindow
    scan_service: ScanApplicationService
    config_service: HardwareConfigurationService
    presenter: ScanPresenter
    motion_port: FakeMotionPort
    acquisition_port: FakeAcquisitionPort
    event_bus: InMemoryEventBus

class TestEnvironment:
    """
    Component that replicates the bootstrap logic of main.py for TESTING purposes.
    Allows creating a full application stack, running it, and tearing it down cleanly.
    """
    
    def __init__(self):
        self.context: Optional[TestContext] = None
        self._threads_at_start = []

    def setup(self):
        """
        Bootstrap the application in Mock mode.
        """
        self._threads_at_start = threading.enumerate()
        
        # 1. PyQt Application
        # Check if QApp already exists (e.g. from previous tests)
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
            
        # 2. Infrastructure
        event_bus = InMemoryEventBus()
        
        # 3. Mocks
        # Inject event_bus here!
        motion_port = FakeMotionPort(event_bus=event_bus)
        acquisition_port = FakeAcquisitionPort()
        init_port = FakeHardwareInitializationPort()
        mock_provider = FakeHardwareConfigProvider("mock_hardware")
        
        # 4. Services
        config_service = HardwareConfigurationService([mock_provider])
        scan_executor = StepScanExecutor(motion_port, acquisition_port, event_bus)
        scan_service = ScanApplicationService(motion_port, acquisition_port, event_bus, scan_executor)
        
        # Mocking other services for MainWindow requirements
        mock_excitation_service = MagicMock()
        mock_continuous_service = MagicMock()
        
        # 5. UI Presenters
        scan_presenter = ScanPresenter(scan_service, config_service)
        excitation_presenter = ExcitationPresenter(mock_excitation_service)
        continuous_presenter = ContinuousAcquisitionPresenter(mock_continuous_service, event_bus)
        
        # 6. MainWindow
        main_window = MainWindow(scan_presenter, excitation_presenter, continuous_presenter)
        
        self.context = TestContext(
            app=app,
            main_window=main_window,
            scan_service=scan_service,
            config_service=config_service,
            presenter=scan_presenter,
            motion_port=motion_port,
            acquisition_port=acquisition_port,
            event_bus=event_bus
        )
        return self.context

    def teardown(self):
        """
        Clean up resources.
        """
        if self.context:
            self.context.main_window.close()
            # If we had a thread running for scan, ensuring it stops:
            if self.context.scan_service._current_scan:
                 self.context.scan_service.cancel_scan()
            
            # Explicitly wait for the presenter's thread to finish
            # Accessing private member for testing purposes is acceptable here
            if hasattr(self.context.presenter, '_scan_thread') and self.context.presenter._scan_thread:
                if self.context.presenter._scan_thread.is_alive():
                    # Wait for it to finish (join)
                    self.context.presenter._scan_thread.join(timeout=2.0)
            
            # Wait a bit for other threads to close
            time.sleep(0.1) 
            self.context = None

    def check_leakages(self):
        """
        Verify that no new threads are left running compared to start.
        """
        current_threads = threading.enumerate()
        
        new_threads = [t for t in current_threads if t not in self._threads_at_start]
        # Ignore pydev/debugger threads if present
        leaked_threads = [t for t in new_threads if "pydev" not in t.name and "MainThread" not in t.name]
        
        if leaked_threads:
            print(f"WARNING: Potential Thread Leakage detected! {len(leaked_threads)} threads left running.")
            for t in leaked_threads:
                print(f" - Leaked Thread: {t.name} (Daemon: {t.daemon})")
            return False
        
        return True
