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
from infrastructure.mocks.adapter_mock_i_acquisition_port import RandomNoiseAcquisitionPort
from infrastructure.mocks.adapter_mock_i_excitation_port import MockExcitationPort
from infrastructure.mocks.adapter_mock_excitation_aware_acquisition import ExcitationAwareAcquisitionPort
from infrastructure.mocks.adapter_mock_i_motion_port import MockMotionPort
from infrastructure.mocks.adapter_mock_i_continuous_acquisition_executor import MockContinuousAcquisitionExecutor

# --- Interface V2 ---
# --- Interface V2 ---
from interface_v2.shell.dashboard import Dashboard
from interface_v2.presenters.motion_presenter import MotionPresenter
from interface_v2.presenters.excitation_presenter import ExcitationPresenter
from interface_v2.presenters.continuous_acquisition_presenter import ContinuousAcquisitionPresenter
from interface_v2.presenters.sensor_transformation_presenter import SensorTransformationPresenter

# --- Transformation Service ---
from application.services.transformation_service.transformation_service import TransformationService


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
    
    # Create base acquisition port and excitation port
    # Noise std = 0.05 (5% of typical signal amplitude of 1.0)
    base_acquisition_port = RandomNoiseAcquisitionPort(noise_std=0.01)
    excitation_port = MockExcitationPort()
    
    # Wrap acquisition port with excitation-aware wrapper
    # phase_default_ratio: ratio between real (in-phase) and imaginary (quadrature) components
    # 0.9 = 90% real, 10% quadrature (default)
    # 1.0 = 100% real, 0% quadrature (all offset on in-phase)
    # 0.5 = 50% real, 50% quadrature (equal distribution)
    acquisition_port = ExcitationAwareAcquisitionPort(
        base_acquisition_port=base_acquisition_port,
        excitation_port=excitation_port,
        real_ratio=0.9,
        offset_scale=1.0  # Adjust magnitude of signal
    )
    
    # --- SIMULATION CONFIGURATION ---
    # Simulate a physically rotated sensor (cube orientation)
    # Rotation: arctan(1/sqrt(2)) on fixed X axis, 45° on fixed Y axis
    import math
    theta_x_deg = math.degrees(math.atan(1 / math.sqrt(2)))  # ~35.26°
    theta_y_deg = 45.0
    acquisition_port.set_sensor_orientation(theta_x_deg, theta_y_deg, 0.0)
    # --------------------------------
    
    continuous_executor = MockContinuousAcquisitionExecutor(event_bus)
    
    print("  [motion] -> mock")
    print("  [acquisition] -> mock (with excitation-aware wrapper)")
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
    
    # Transformation Service (Shared State)
    transformation_service = TransformationService()
    
    # 5. Create Dashboard (View Shell)
    print("\n--- Creating Dashboard ---")
    dashboard = Dashboard()

    # 6. Create UI Presenters (Interface V2)
    # Note: Presenters now depend on Services AND Dashboard panels (Views)
    # But some Presenters are View-agnostic? 
    # ContinuousAcquisitionPresenter is View-Agnostic regarding instantiation, but needs wiring later.
    # SensorTransformationPresenter NEEDS the panel in constructor.
    print("\n--- Creating UI Presenters ---")
    
    motion_presenter = MotionPresenter(motion_control_service, event_bus)
    excitation_presenter = ExcitationPresenter(excitation_service)
    
    # Continuous Presenter needs Transformation Service now
    continuous_presenter = ContinuousAcquisitionPresenter(continuous_service, event_bus, transformation_service)
    
    # Transformation Presenter needs Panel + Service
    transformation_presenter = SensorTransformationPresenter(dashboard.panels["transformation"], transformation_service)
    
    
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
    print(f"  [excitation] Connecting signal: excitation_panel.excitation_changed -> excitation_presenter.on_excitation_changed")
    excitation_panel.excitation_changed.connect(excitation_presenter.on_excitation_changed)
    print("  [excitation] wired")
    
    # Continuous Acquisition Panel
    continuous_panel = dashboard.panels["continuous"]
    continuous_panel.acquisition_start_requested.connect(continuous_presenter.on_acquisition_start_requested)
    continuous_panel.acquisition_stop_requested.connect(continuous_presenter.on_acquisition_stop_requested)
    continuous_panel.parameters_updated.connect(continuous_presenter.on_parameters_updated)
    
    # Calibration & Transformation Wiring
    continuous_panel.calibrate_noise_requested.connect(continuous_presenter.calibrate_noise)
    continuous_panel.calibrate_phase_requested.connect(continuous_presenter.calibrate_phase)
    continuous_panel.calibrate_primary_requested.connect(continuous_presenter.calibrate_primary)
    continuous_panel.reset_calibration_requested.connect(continuous_presenter.reset_calibration)
    
    continuous_panel.apply_rotation_toggled.connect(continuous_presenter.on_rotation_toggled)
    
    continuous_presenter.acquisition_started.connect(continuous_panel.on_acquisition_started)
    continuous_presenter.acquisition_stopped.connect(continuous_panel.on_acquisition_stopped)
    continuous_presenter.sample_acquired.connect(continuous_panel.on_sample_acquired)
    continuous_presenter.angles_updated.connect(continuous_panel.update_angles_display)
    print("  [continuous] wired")
    
    print("  [transformation] wired (via constructor)")
    
    # 8. Show Dashboard
    print("\n--- Launching Dashboard ---")
    dashboard.show()
    print("Dashboard launched successfully!")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()