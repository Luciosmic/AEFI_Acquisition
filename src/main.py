import os
import sys
from pathlib import Path

# Add src to sys.path to allow imports from any location
root_dir = Path(__file__).parent.resolve()
# main.py is in src, so its parent is the project root if we want src/top_level
# Actually, since main.py is in src, it can import interface/application directly.
# But for consistency with other scripts that might run from root:
sys.path.insert(0, str(root_dir))

from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt, QTimer, Signal

# --- Domain & Application Services ---
from application.services.scan_application_service.scan_application_service import ScanApplicationService
from application.services.excitation_configuration_service.excitation_configuration_service import ExcitationConfigurationService
from application.services.continuous_acquisition_service.continuous_acquisition_service import ContinuousAcquisitionService
from application.services.motion_control_service.motion_control_service import MotionControlService

# --- Infrastructure ---
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.execution.step_scan_executor import StepScanExecutor
from infrastructure.persistence.csv_scan_export_port import CsvScanExportPort
from infrastructure.persistence.hdf5_scan_export_port import Hdf5ScanExportPort
from application.services.scan_application_service.scan_export_service import ScanExportService

# --- Adapters (Mocks) ---
from infrastructure.mocks.adapter_mock_i_acquisition_port import RandomNoiseAcquisitionPort
from infrastructure.mocks.adapter_mock_i_excitation_port import MockExcitationPort
from infrastructure.mocks.adapter_mock_excitation_aware_acquisition import ExcitationAwareAcquisitionPort
from infrastructure.mocks.adapter_mock_i_motion_port import MockMotionPort
from infrastructure.mocks.adapter_mock_i_continuous_acquisition_executor import MockContinuousAcquisitionExecutor
from infrastructure.mocks.adapter_mock_i_hardware_initialization_port import MockHardwareInitializationPort

# --- System Lifecycle ---
from application.services.system_lifecycle_service.system_lifecycle_service import (
    SystemStartupApplicationService,
    SystemShutdownApplicationService,
    StartupConfig
)

# --- Interface V2 ---
# --- Interface V2 ---
from interface.shell.dashboard import Dashboard
from interface.presenters.motion_presenter import MotionPresenter
from interface.presenters.excitation_presenter import ExcitationPresenter
from interface.presenters.continuous_acquisition_presenter import ContinuousAcquisitionPresenter
from interface.presenters.sensor_transformation_presenter import SensorTransformationPresenter
from interface.presenters.scan_presenter import ScanPresenter

# --- Transformation Service ---
from application.services.transformation_service.transformation_service import TransformationService

# --- Hardware Configuration ---
from application.services.hardware_configuration_service.hardware_configuration_service import HardwareConfigurationService
from application.services.hardware_configuration_service.i_hardware_advanced_configurator import IHardwareAdvancedConfigurator
from interface.presenters.hardware_advanced_config_presenter import HardwareAdvancedConfigPresenter
from interface.styles.theme import apply_dark_theme

def main():
    """
    Main entry point for Interface V2.
    Composition root that builds the dependency graph.
    """
    # 1. Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("AEFI Acquisition - Interface V2")
    
    # Apply Dark Theme
    apply_dark_theme(app)
    
    # 2. Configuration: Hardware Adapter Registry
    # Simple dict-based configuration: port_name -> adapter_type ("mock" | "real")
    HARDWARE_CONFIG = {
        "motion": "mock",        # "mock" | "real"
        "acquisition": "mock",   # "mock" | "real"
        "excitation": "mock",    # "mock" | "real"
        "continuous": "mock",    # "mock" | "real"
    }
    print("--- Starting Interface V2 ---")
    print(f"Hardware Config: {HARDWARE_CONFIG}")
    
    # 3. Infrastructure Setup (Event Bus)
    event_bus = InMemoryEventBus()
    
    # 4. Instantiate Adapters
    print("\n--- Initializing Hardware Adapters ---")
    motion_port = None
    base_acquisition_port = None
    excitation_port = None
    continuous_executor = None
    lifecycle_adapters = []
    
    # --- Motion (Arcus) ---
    if HARDWARE_CONFIG["motion"] == "real":
        from infrastructure.hardware.arcus_performax_4EX.composition_root_arcus import ArcusCompositionRoot
        print("  [motion] -> real (ArcusCompositionRoot)")
        arcus_root = ArcusCompositionRoot(event_bus=event_bus)
        motion_port = arcus_root.motion
        lifecycle_adapters.append(arcus_root.lifecycle)
    else:
        print("  [motion] -> mock")
        motion_port = MockMotionPort(event_bus=event_bus, motion_delay_ms=50.0)
    
    # --- Acquisition (ADS131) ---
    mcu_root = None
    if HARDWARE_CONFIG["acquisition"] == "real":
        from infrastructure.hardware.micro_controller.mcu_composition_root import MCUCompositionRoot
        print("  [acquisition] -> real (MCUCompositionRoot)")
        # Note: MCUCompositionRoot needs event_bus for continuous acquisition
        mcu_root = MCUCompositionRoot(event_bus=event_bus)
        base_acquisition_port = mcu_root.acquisition
        lifecycle_adapters.append(mcu_root.lifecycle)
        continuous_executor = mcu_root.continuous
        
        # --- Excitation (AD9106 - part of MCU) ---
        if HARDWARE_CONFIG["excitation"] == "real":
            excitation_port = mcu_root.excitation
            print("  [excitation] -> real (from MCUCompositionRoot)")
    else:
        print("  [acquisition] -> mock")
        # Noise std = 0.01 (1% of typical signal amplitude of 1.0)
        base_acquisition_port = RandomNoiseAcquisitionPort(noise_std=0.01)
    
    # --- Excitation (Fallback / Mock) ---
    if HARDWARE_CONFIG["excitation"] == "real":
        # If we are here, it means we wanted real excitation but didn't get it from MCU (e.g. acquisition=mock)
        if excitation_port is None:
            print("  [excitation] -> WARNING: Cannot use real excitation without MCU (acquisition=real required)")
            print("  [excitation] -> Falling back to mock")
            excitation_port = MockExcitationPort()
    else:
        if excitation_port is None:
            print("  [excitation] -> mock")
            excitation_port = MockExcitationPort()
    
    # --- Continuous Acquisition ---
    if HARDWARE_CONFIG["continuous"] == "real":
        if continuous_executor is None:
            print("  [continuous] -> WARNING: Cannot use real continuous without MCU (acquisition=real required)")
            print("  [continuous] -> Falling back to mock")
            continuous_executor = MockContinuousAcquisitionExecutor(event_bus)
        else:
            print("  [continuous] -> real (from MCUCompositionRoot)")
    else:
        if continuous_executor is None:
            print("  [continuous] -> mock")
            continuous_executor = MockContinuousAcquisitionExecutor(event_bus)
    
    # --- Wrap acquisition port with excitation-aware wrapper (only for mocks) ---
    # This simulates the physical coupling between excitation and acquisition
    # For real hardware, the coupling is physical and doesn't need simulation
    if HARDWARE_CONFIG["acquisition"] == "mock" and HARDWARE_CONFIG["excitation"] == "mock":
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
        print("  [acquisition] -> wrapped with ExcitationAwareAcquisitionPort (simulation)")
    else:
        # Use base acquisition port directly for real hardware
        acquisition_port = base_acquisition_port
        print("  [acquisition] -> using base port directly (real hardware)")
    
    # 5. Create Hardware Initialization Port
    if lifecycle_adapters:
        from infrastructure.hardware.composite_hardware_initialization_port import CompositeHardwareInitializationPort
        init_port = CompositeHardwareInitializationPort(lifecycle_adapters)
    else:
        init_port = MockHardwareInitializationPort()
    
    # 6. Create Application Services
    print("\n--- Creating Application Services ---")
    
    # Scan Executor (Infrastructure service)
    scan_executor = StepScanExecutor(motion_port, acquisition_port, event_bus)
    
    # Scan Application Service
    scan_service = ScanApplicationService(motion_port, acquisition_port, event_bus, scan_executor)
    
    # Scan Export Service
    csv_export_port = CsvScanExportPort()
    hdf5_export_port = Hdf5ScanExportPort()
    scan_export_service = ScanExportService(event_bus, csv_export_port, hdf5_export_port)
    
    # Excitation Service
    excitation_service = ExcitationConfigurationService(excitation_port)
    
    # Continuous Acquisition Service - PASS acquisition_port NOT event_bus!
    continuous_service = ContinuousAcquisitionService(continuous_executor, acquisition_port)
    
    # Motion Control Service
    motion_control_service = MotionControlService(motion_port, event_bus)
    
    # Transformation Service (Shared State)
    transformation_service = TransformationService(event_bus)
    
    # Hardware Configuration Service
    print("\n--- Creating Hardware Configuration Service ---")
    configurators: list[IHardwareAdvancedConfigurator] = []
    
    # Add configurators from composition roots if real hardware is used
    if HARDWARE_CONFIG["motion"] == "real" and 'arcus_root' in locals():
        configurators.append(arcus_root.config)
        print("  [config] -> added Arcus configurator")
    
    if HARDWARE_CONFIG["acquisition"] == "real" and mcu_root:
        configurators.extend(mcu_root.configurators)
        print(f"  [config] -> added {len(mcu_root.configurators)} MCU configurator(s)")
    
    hardware_config_service = HardwareConfigurationService(configurators)
    print(f"  [config] -> service created with {len(configurators)} configurator(s)")
    
    # 7. Create Lifecycle Services (only if real hardware is used)
    # For mock-only, we skip startup
    use_startup = len(lifecycle_adapters) > 0
    
    if use_startup:
        # Import lifecycle presenter (Interface V2 - PySide6)
        from interface.ui_system_lifecycle.presenter_system_lifecycle import SystemLifecyclePresenter
        
        lifecycle_presenter = SystemLifecyclePresenter()
        startup_service = SystemStartupApplicationService(
            hardware_initializer=init_port,
            calibration_service=None,
            event_bus=event_bus,
            output_port=lifecycle_presenter
        )
        
        shutdown_service = SystemShutdownApplicationService(
            scan_service=scan_service,
            acquisition_service=None,
            hardware_initializer=init_port,
            event_bus=event_bus,
            output_port=lifecycle_presenter
        )
        lifecycle_presenter.set_services(startup_service, shutdown_service)
    
    # 8. Create Dashboard (View Shell)
    print("\n--- Creating Dashboard ---")
    dashboard = Dashboard()

    # 9. Create UI Presenters (Interface V2)
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
    
    
    # Scan Presenter
    scan_presenter = ScanPresenter(scan_service, scan_export_service, event_bus)
    
    # Hardware Advanced Config Presenter
    hardware_config_presenter = HardwareAdvancedConfigPresenter(hardware_config_service)
    
    # 10. Wire Presenters to Panels
    print("--- Wiring Presenters to Panels ---")
    
    # Motion Panel
    motion_panel = dashboard.panels["motion"]
    motion_panel.jog_requested.connect(motion_presenter.on_jog_requested)
    motion_panel.move_to_requested.connect(motion_presenter.on_move_to_requested)
    motion_panel.move_both_requested.connect(motion_presenter.on_move_both_requested)
    motion_panel.move_to_center_requested.connect(motion_presenter.on_move_to_center_requested)
    motion_panel.home_requested.connect(motion_presenter.on_home_requested)
    motion_panel.stop_requested.connect(motion_presenter.on_stop_requested)
    motion_panel.estop_requested.connect(motion_presenter.on_estop_requested)
    
    motion_presenter.position_updated.connect(motion_panel.update_position)
    motion_presenter.status_updated.connect(motion_panel.update_status)
    motion_presenter.jog_enabled_changed.connect(motion_panel.set_jog_enabled)
    motion_presenter.limits_updated.connect(motion_panel.set_axis_limits)
    
    # Initialize presenter to fetch limits
    motion_presenter.initialize()
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
    
    print("  [continuous] wired")
    
    # Scan Panels Wiring
    scan_control_panel = dashboard.panels["scan_control"]
    scan_visualization_panel = dashboard.panels["scan_viz"]
    
    # Control -> Presenter
    scan_control_panel.scan_start_requested.connect(scan_presenter.on_scan_start_requested)
    scan_control_panel.scan_stop_requested.connect(scan_presenter.on_scan_stop_requested)
    scan_control_panel.scan_pause_requested.connect(scan_presenter.on_scan_pause_requested)
    scan_control_panel.scan_resume_requested.connect(scan_presenter.on_scan_resume_requested)
    
    # Presenter -> Control
    scan_presenter.status_updated.connect(scan_control_panel.update_status)
    scan_presenter.scan_started.connect(lambda scan_id, _: scan_control_panel.on_scan_started(scan_id))
    scan_presenter.scan_completed.connect(scan_control_panel.on_scan_completed)
    scan_presenter.scan_failed.connect(scan_control_panel.on_scan_failed)
    scan_presenter.scan_cancelled.connect(scan_control_panel.on_scan_cancelled)
    scan_presenter.scan_paused.connect(scan_control_panel.on_scan_paused)
    scan_presenter.scan_resumed.connect(scan_control_panel.on_scan_resumed)
    
    # Presenter -> Visualization
    def on_scan_started_viz(scan_id, config):
        scan_visualization_panel.initialize_scan(
            config["x_min"], config["x_max"], config["x_nb_points"],
            config["y_min"], config["y_max"], config["y_nb_points"]
        )
        
    def on_scan_progress_viz(current, total, data):
        # data has 'x', 'y', 'value'
        scan_visualization_panel.update_data_point_from_position(
            data["x"], data["y"], data["value"]
        )

    scan_presenter.scan_started.connect(on_scan_started_viz)
    scan_presenter.scan_progress.connect(on_scan_progress_viz)
    print("  [scan] wired")

    # Hardware Advanced Config Panel Wiring
    hardware_config_panel = dashboard.panels["hardware_config"]
    
    # Presenter -> Panel
    hardware_config_presenter.hardware_list_updated.connect(hardware_config_panel.set_hardware_list)
    hardware_config_presenter.specs_loaded.connect(hardware_config_panel.set_parameter_specs)
    hardware_config_presenter.status_message.connect(hardware_config_panel.set_status_message)
    hardware_config_presenter.config_applied.connect(lambda hw_id: hardware_config_panel.set_status_message(f"Configuration applied to {hw_id}"))
    
    # Panel -> Presenter
    hardware_config_panel.hardware_selected.connect(hardware_config_presenter.select_hardware)
    hardware_config_panel.apply_requested.connect(hardware_config_presenter.apply_configuration)
    hardware_config_panel.save_default_requested.connect(hardware_config_presenter.save_configuration_as_default)
    
    # Initialize: refresh hardware list on startup
    hardware_config_presenter.refresh_hardware_list()
    
    print("  [hardware_config] wired")

    print("  [transformation] wired (via constructor)")
    
    # 11. Startup Sequence (if real hardware) or Direct Launch (if mocks only)
    if use_startup:
        # Import startup view (Interface V2 - PySide6)
        from interface.ui_system_lifecycle.view_startup import StartupView
        
        startup_view = StartupView(lifecycle_presenter)
        
        # Define startup completion handler
        dashboard_window = None
        
        def on_startup_finished(success: bool, errors: list):
            nonlocal dashboard_window
            if success:
                print("Hardware initialization successful.")
                startup_view.close()
                
                # Show Dashboard
                print("\n--- Launching Dashboard ---")
                dashboard_window = dashboard
                dashboard_window.show()
                print("Dashboard launched successfully!")
            else:
                print(f"CRITICAL: Hardware initialization failed: {errors}")
                # StartupView will display the error
                # User can close the window manually
        
        lifecycle_presenter.startup_finished.connect(on_startup_finished)
        
        # Show startup screen and start initialization
        startup_view.show()
    else:
        # No startup needed for mocks - launch dashboard directly
        print("\n--- Launching Dashboard ---")
        dashboard.show()
        print("Dashboard launched successfully!")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()