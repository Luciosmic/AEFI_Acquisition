import os
import sys
from pathlib import Path

# Add src to sys.path to allow imports from any location
root_dir = Path(__file__).parent.resolve()
src_dir = root_dir / "src"
sys.path.insert(0, str(src_dir))

from PySide6.QtWidgets import QApplication

# --- Domain & Application Services ---
from application.services.scan_application_service.scan_application_service import ScanApplicationService
from application.services.excitation_configuration_service.excitation_configuration_service import ExcitationConfigurationService
from application.services.continuous_acquisition_service.continuous_acquisition_service import ContinuousAcquisitionService
from application.services.motion_control_service.motion_control_service import MotionControlService

# --- Infrastructure ---
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.execution.step_scan_executor import StepScanExecutor

# --- Adapters (Mocks) ---
from infrastructure.mocks.adapter_mock_i_motion_port import MockMotionPort
from infrastructure.mocks.adapter_mock_i_acquisition_port import RandomNoiseAcquisitionPort
from infrastructure.mocks.adapter_mock_i_excitation_port import MockExcitationPort
from infrastructure.mocks.adapter_mock_i_continuous_acquisition_executor import MockContinuousAcquisitionExecutor

# --- Interface V2 ---
from interface_v2.shell.dashboard import Dashboard
from interface_v2.presenters.motion_presenter import MotionPresenter
from interface_v2.presenters.excitation_presenter import ExcitationPresenter
from interface_v2.presenters.continuous_acquisition_presenter import ContinuousAcquisitionPresenter


def main():
    """
    Main entry point for Interface V2 with mock infrastructure.
    Composition root that builds the dependency graph.
    """
    # 1. Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("AEFI Acquisition - Interface V2")
    
    print("--- Starting Interface V2 ---")
    print("Hardware Config: ALL MOCKS")
    
    # 2. Infrastructure Setup (Event Bus)
    event_bus = InMemoryEventBus()
    
    # 3. Instantiate Adapters (All Mocks for now)
    print("\n--- Initializing Mock Adapters ---")
    motion_port = MockMotionPort(event_bus=event_bus, motion_delay_ms=50.0)
    acquisition_port = RandomNoiseAcquisitionPort()
    excitation_port = MockExcitationPort()
    continuous_executor = MockContinuousAcquisitionExecutor(event_bus)
    
    print("  [motion] -> mock")
    print("  [acquisition] -> mock")
    print("  [excitation] -> mock")
    print("  [continuous] -> mock")
    
    # 4. Create Application Services
    print("\n--- Creating Application Services ---")
    
    # Scan Executor (Infrastructure service)
    scan_executor = StepScanExecutor(motion_port, acquisition_port, event_bus)
    
    # Scan Application Service
    scan_service = ScanApplicationService(motion_port, acquisition_port, event_bus, scan_executor)
    
    # Excitation Service
    excitation_service = ExcitationConfigurationService(excitation_port)
    
    # Continuous Acquisition Service - PASS acquisition_port NOT event_bus!
    continuous_service = ContinuousAcquisitionService(continuous_executor, acquisition_port)
    
    # Motion Control Service
    motion_control_service = MotionControlService(motion_port, event_bus)
    
    # 5. Create UI Presenters (Interface V2)
    print("\n--- Creating UI Presenters ---")
    motion_presenter = MotionPresenter(motion_control_service, event_bus)
    excitation_presenter = ExcitationPresenter(excitation_service)
    continuous_presenter = ContinuousAcquisitionPresenter(continuous_service, event_bus)
    
    # 6. Create Dashboard
    print("\n--- Creating Dashboard ---")
    dashboard = Dashboard()
    
    # 7. Wire Presenters to Panels
    print("--- Wiring Presenters to Panels ---")
    
    # Motion Panel
    motion_panel = dashboard.panels["motion"]
    motion_panel.jog_requested.connect(motion_presenter.on_jog_requested)
    motion_panel.move_to_requested.connect(motion_presenter.on_move_to_requested)
    motion_panel.home_requested.connect(motion_presenter.on_home_requested)
    motion_panel.stop_requested.connect(motion_presenter.on_stop_requested)
    motion_panel.estop_requested.connect(motion_presenter.on_estop_requested)
    
    motion_presenter.position_updated.connect(motion_panel.update_position)
    motion_presenter.status_updated.connect(motion_panel.update_status)
    print("  [motion] wired")
    
    # Excitation Panel
    excitation_panel = dashboard.panels["excitation"]
    excitation_panel.excitation_changed.connect(excitation_presenter.on_excitation_changed)
    print("  [excitation] wired")
    
    # Continuous Acquisition Panel
    continuous_panel = dashboard.panels["continuous"]
    continuous_panel.acquisition_start_requested.connect(continuous_presenter.on_acquisition_start_requested)
    continuous_panel.acquisition_stop_requested.connect(continuous_presenter.on_acquisition_stop_requested)
    continuous_panel.parameters_updated.connect(continuous_presenter.on_parameters_updated)
    
    # Calibration Wiring
    continuous_panel.calibrate_noise_requested.connect(continuous_presenter.calibrate_noise)
    continuous_panel.calibrate_phase_requested.connect(continuous_presenter.calibrate_phase)
    continuous_panel.calibrate_primary_requested.connect(continuous_presenter.calibrate_primary)
    continuous_panel.reset_calibration_requested.connect(continuous_presenter.reset_calibration)
    
    continuous_presenter.acquisition_started.connect(continuous_panel.on_acquisition_started)
    continuous_presenter.acquisition_stopped.connect(continuous_panel.on_acquisition_stopped)
    continuous_presenter.sample_acquired.connect(continuous_panel.on_sample_acquired)
    print("  [continuous] wired")
    
    # 8. Show Dashboard
    print("\n--- Launching Dashboard ---")
    dashboard.show()
    print("Dashboard launched successfully!")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()