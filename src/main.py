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
from PySide6.QtGui import QIcon

# --- Domain & Application Services ---
from application.services.scan_application_service.scan_application_service import (
    ScanApplicationService,
    make_electric_field_probe_channel,
)
from application.services.excitation_configuration_service.excitation_configuration_service import ExcitationConfigurationService
from application.services.aefi_acquisition_service.aefi_acquisition_service import AefiAcquisitionService
from application.services.motion_control_service.motion_control_service import MotionControlService
from application.services.electric_field_probe_service.electric_field_probe_service import ElectricFieldProbeService

# --- Infrastructure ---
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.execution.thread_pool_task_runner import ThreadPoolTaskRunner
from infrastructure.execution.event_bus_motion_synchronizer import EventBusMotionSynchronizer
from infrastructure.persistence.csv_scan_export_port import CsvScanExportPort
from infrastructure.persistence.hdf5_scan_export_port import Hdf5ScanExportPort
from infrastructure.persistence.acquisition_snapshot_reader import AcquisitionSnapshotReader
from infrastructure.post_processing.aefi_post_processor_port import AefiPostProcessorPort
from application.services.scan_export_service.scan_export_service import ScanExportService

# --- Adapters (Mocks) ---
from infrastructure.mocks.adapter_mock_i_acquisition_port import RandomNoiseAcquisitionPort
from infrastructure.mocks.adapter_mock_i_excitation_port import MockExcitationPort
from infrastructure.mocks.adapter_mock_excitation_aware_acquisition import ExcitationAwareAcquisitionPort
from infrastructure.mocks.adapter_mock_i_motion_port import MockMotionPort
from infrastructure.mocks.adapter_mock_i_aefi_acquisition_executor import MockAefiAcquisitionExecutor
from infrastructure.execution.electric_field_probe_acquisition_executor import ElectricFieldProbeAcquisitionExecutor
from infrastructure.mocks.adapter_mock_i_hardware_initialization_port import MockHardwareInitializationPort
from infrastructure.hardware.narda_ep600.adapter_electric_field_probe_port import NardaEP601ProbeAdapter
from infrastructure.hardware.narda_ep600.fake.fake_electric_field_probe_adapter import FakeElectricFieldProbeAdapter

# --- System Lifecycle ---
from application.services.system_lifecycle_service.system_lifecycle_service import (
    SystemStartupApplicationService,
    SystemShutdownApplicationService,
    StartupConfig
)
from interface.ui_system_lifecycle.presenter_system_lifecycle import SystemLifecyclePresenter
from interface.ui_system_lifecycle.view_startup import StartupView

# --- Interface ---
from interface.shell.dashboard import Dashboard
from interface.widgets.panels.logs_panel import LogsPanel, install_console_capture
from interface.presenters.motion_presenter import MotionPresenter
from interface.presenters.excitation_presenter import ExcitationPresenter
from interface.presenters.continuous_acquisition_presenter import ContinuousAcquisitionPresenter
from interface.presenters.electric_field_probe_presenter import ElectricFieldProbePresenter
from interface.presenters.sensor_transformation_presenter import SensorTransformationPresenter
from interface.presenters.scan_presenter import ScanPresenter

# --- Transformation Service ---
from application.services.transformation_service.transformation_service import TransformationService

# --- Hardware Configuration ---
from application.services.hardware_configuration_service.hardware_configuration_service import HardwareConfigurationService
from application.services.hardware_configuration_service.ports.i_hardware_advanced_configurator import IHardwareAdvancedConfigurator
from interface.presenters.hardware_advanced_config_presenter import HardwareAdvancedConfigPresenter
from interface.styles.theme import apply_dark_theme

def main():
    """
    Main entry point for Interface V2.
    Composition root that builds the dependency graph.
    """
    # 0. Bootstrap runtime configs (.aefi_acquisition/configs/ ← config_templates/)
    from infrastructure.config.config_bootstrapper import ConfigBootstrapper
    repo_root = root_dir.parent
    bootstrapper = ConfigBootstrapper(
        templates_dir=repo_root / "config_templates",
        runtime_dir=repo_root / ".aefi_acquisition" / "configs",
    )
    seeded = bootstrapper.ensure_configs_exist()
    if seeded:
        print(f"[bootstrap] Configs initialisées depuis templates : {seeded}")

    # 1. Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("AEFI Acquisition - Interface V2")
    app.setWindowIcon(QIcon(str(root_dir / "interface" / "assets" / "app_icon.ico")))

    if sys.platform == "win32":
        import ctypes
        # Windows groups taskbar entries by AppUserModelID; without it, python.exe's own icon wins.
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("AEFI.Acquisition.InterfaceV2")
    
    # Apply Dark Theme
    apply_dark_theme(app)

    # 1bis. Logs panel + splash: shown first, capture everything from here on
    splash_logs_panel = LogsPanel()
    log_stream = install_console_capture(splash_logs_panel)

    lifecycle_presenter = SystemLifecyclePresenter()
    startup_view = StartupView(lifecycle_presenter, logs_panel=splash_logs_panel)
    startup_view.show()
    startup_view.set_phase("Configuration matérielle...")
    app.processEvents()

    # 2. Configuration: Hardware Adapter Registry
    # Simple dict-based configuration: port_name -> adapter_type ("mock" | "real")
    HARDWARE_CONFIG = {
        "motion": "real",        # "mock" | "real"
        "acquisition": "real",   # "mock" | "real"
        "excitation": "real",    # "mock" | "real"
        "continuous": "real",    # "mock" | "real"
        "electric_field_probe": "real",  # "mock" | "real" — picks the adapter only, connection is manual (cf. panel)
    }
    NARDA_COM_PORT = "COM8"  # cf. config_templates/electric_field_probe_config.json
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
            continuous_executor = MockAefiAcquisitionExecutor(event_bus)
        else:
            print("  [continuous] -> real (from MCUCompositionRoot)")
    else:
        if continuous_executor is None:
            print("  [continuous] -> mock")
            continuous_executor = MockAefiAcquisitionExecutor(event_bus)
    
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
    
    # --- Electric Field Probe (Narda EP-601) ---
    # Deliberately NOT added to lifecycle_adapters: this probe is auto-off and
    # times out often, so it must never block or fail app startup. Connection
    # is a manual action from the panel (Connect button), not a startup step.
    if HARDWARE_CONFIG["electric_field_probe"] == "real":
        print(f"  [electric_field_probe] -> real (Narda EP-601 on {NARDA_COM_PORT})")
        probe_port = NardaEP601ProbeAdapter(port=NARDA_COM_PORT)
    else:
        print("  [electric_field_probe] -> mock")
        probe_port = FakeElectricFieldProbeAdapter()

    # 5. Create Hardware Initialization Port
    if lifecycle_adapters:
        from infrastructure.hardware.composite_hardware_initialization_port import CompositeHardwareInitializationPort
        init_port = CompositeHardwareInitializationPort(lifecycle_adapters)
    else:
        init_port = MockHardwareInitializationPort()
    
    # 6. Create Application Services
    startup_view.set_phase("Services applicatifs...")
    app.processEvents()
    print("\n--- Creating Application Services ---")
    
    # Shared task runner + motion synchronizer (one instance, reused by both services)
    task_runner = ThreadPoolTaskRunner()
    motion_sync = EventBusMotionSynchronizer(event_bus)

    # Continuous Acquisition Service - PASS acquisition_port NOT event_bus!
    # Built before ScanApplicationService: the scan drives its acquisition
    # through this service's stream (start/stop + subscribe) instead of
    # pulling acquisition_port directly, so it needs the service, not the
    # raw port.
    continuous_service = AefiAcquisitionService(continuous_executor, acquisition_port)

    # Electric Field Probe Service
    # Same reasoning: built before ScanApplicationService, which subscribes
    # to its sample stream rather than pulling probe_port directly.
    electric_field_probe_executor = ElectricFieldProbeAcquisitionExecutor(event_bus)
    electric_field_probe_service = ElectricFieldProbeService(
        executor=electric_field_probe_executor,
        probe_port=probe_port,
        event_bus=event_bus,
    )

    # Scan Application Service — auxiliary probes (currently: Narda EF probe)
    # are registered as blocking channels; see AuxiliaryProbeChannel for what
    # "blocking" means and make_electric_field_probe_channel for the Narda wiring.
    narda_channel = make_electric_field_probe_channel(
        probe_port=probe_port,
        probe_service=electric_field_probe_service,
        event_bus=event_bus,
    )
    scan_service = ScanApplicationService(
        motion_port, continuous_service, event_bus,
        task_runner=task_runner,
        motion_sync=motion_sync,
        auxiliary_probes=[narda_channel],
    )

    # Excitation Service
    excitation_service = ExcitationConfigurationService(excitation_port, event_bus)

    # Scan Export Service
    csv_export_port = CsvScanExportPort()
    hdf5_export_port = Hdf5ScanExportPort()
    acquisition_snapshot_port = AcquisitionSnapshotReader()
    post_processing_port = AefiPostProcessorPort()
    scan_export_service = ScanExportService(
        event_bus, csv_export_port, hdf5_export_port,
        excitation_service=excitation_service,
        acquisition_snapshot_port=acquisition_snapshot_port,
        post_processing_port=post_processing_port,
        task_runner=task_runner,
    )

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
    startup_view.set_phase("Construction de l'interface...")
    app.processEvents()
    print("\n--- Creating Dashboard ---")
    dashboard = Dashboard()

    # Dashboard's permanent Logs panel picks up the splash's history so far,
    # then stays live via the same stream for the rest of the app's life.
    dashboard.panels["logs"].text_edit.setPlainText(splash_logs_panel.text_edit.toPlainText())
    log_stream.text_written.connect(dashboard.panels["logs"].append_line)

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

    # Electric Field Probe Presenter
    electric_field_probe_presenter = ElectricFieldProbePresenter(electric_field_probe_service, event_bus)
    
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
    motion_panel.speed_mode_changed.connect(motion_presenter.on_speed_mode_requested)

    motion_presenter.position_updated.connect(motion_panel.update_position)
    motion_presenter.status_updated.connect(motion_panel.update_status)
    motion_presenter.jog_enabled_changed.connect(motion_panel.set_jog_enabled)
    motion_presenter.limits_updated.connect(motion_panel.set_axis_limits)

    # Settings Panel -> Motion Panel (referential mode: limit-switch raw vs. centered/4-quadrants)
    settings_panel = dashboard.panels["settings"]
    settings_panel.motion_referential_changed.connect(motion_panel.set_referential_mode)

    # Initialize presenter to fetch limits
    motion_presenter.initialize()
    motion_presenter.on_speed_mode_requested(motion_panel.get_current_speed_mode())
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
    
    # Calibration & Transformation Wiring
    continuous_panel.calibrate_noise_requested.connect(continuous_presenter.calibrate_noise)
    continuous_panel.calibrate_phase_requested.connect(continuous_presenter.calibrate_phase)
    continuous_panel.calibrate_primary_requested.connect(continuous_presenter.calibrate_primary)
    continuous_panel.reset_calibration_requested.connect(continuous_presenter.reset_calibration)

    # Correction toggles (panel -> presenter)
    continuous_panel.noise_toggled.connect(continuous_presenter.on_noise_toggled)
    continuous_panel.phase_toggled.connect(continuous_presenter.on_phase_toggled)
    continuous_panel.primary_toggled.connect(continuous_presenter.on_primary_toggled)

    # Correction state feedback (presenter -> panel)
    continuous_presenter.correction_states_updated.connect(continuous_panel.update_correction_states)

    continuous_panel.apply_rotation_toggled.connect(continuous_presenter.on_rotation_toggled)
    
    continuous_presenter.acquisition_started.connect(continuous_panel.on_acquisition_started)
    continuous_presenter.acquisition_stopped.connect(continuous_panel.on_acquisition_stopped)
    continuous_presenter.sample_acquired.connect(continuous_panel.on_sample_acquired)
    continuous_presenter.angles_updated.connect(continuous_panel.update_angles_display)
    print("  [continuous] wired")

    # Electric Field Probe Panel
    electric_field_probe_panel = dashboard.panels["electric_field_probe"]
    electric_field_probe_panel.connect_requested.connect(electric_field_probe_presenter.on_connect_requested)
    electric_field_probe_panel.disconnect_requested.connect(electric_field_probe_presenter.on_disconnect_requested)
    electric_field_probe_panel.refresh_battery_requested.connect(electric_field_probe_presenter.on_refresh_battery_requested)
    electric_field_probe_panel.acquisition_start_requested.connect(electric_field_probe_presenter.on_acquisition_start_requested)
    electric_field_probe_panel.acquisition_stop_requested.connect(electric_field_probe_presenter.on_acquisition_stop_requested)
    electric_field_probe_panel.calibrate_noise_requested.connect(electric_field_probe_presenter.calibrate_noise)
    electric_field_probe_panel.reset_calibration_requested.connect(electric_field_probe_presenter.reset_calibration)
    electric_field_probe_panel.noise_toggled.connect(electric_field_probe_presenter.on_noise_toggled)

    electric_field_probe_presenter.probe_connection_changed.connect(electric_field_probe_panel.on_probe_connection_changed)
    electric_field_probe_presenter.probe_axes_defined.connect(electric_field_probe_panel.on_probe_axes_defined)
    electric_field_probe_presenter.acquisition_started.connect(electric_field_probe_panel.on_acquisition_started)
    electric_field_probe_presenter.acquisition_stopped.connect(electric_field_probe_panel.on_acquisition_stopped)
    electric_field_probe_presenter.sample_acquired.connect(electric_field_probe_panel.on_sample_acquired)
    electric_field_probe_presenter.noise_state_updated.connect(electric_field_probe_panel.update_correction_states)
    electric_field_probe_presenter.frequency_correction_changed.connect(electric_field_probe_panel.on_frequency_correction_changed)
    print("  [electric_field_probe] wired")

    # Scan Panels Wiring
    scan_control_panel = dashboard.panels["scan_control"]
    scan_visualization_panel = dashboard.panels["scan_viz"]
    field_scan_visualization_panel = dashboard.panels["field_scan_viz"]
    
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
        # Channel set depends on the connected probe (mono/bi/tri-axial),
        # so it's left empty here and populated lazily from the first point.
        field_scan_visualization_panel.initialize_scan(
            config["x_min"], config["x_max"], config["x_nb_points"],
            config["y_min"], config["y_max"], config["y_nb_points"],
            channels=[]
        )

    def on_scan_progress_viz(current, total, data):
        # data has 'x', 'y', 'value'
        scan_visualization_panel.update_data_point_from_position(
            data["x"], data["y"], data["value"]
        )

    def on_field_scan_progress_viz(current, total, data):
        field_scan_visualization_panel.update_data_point_from_position(
            data["x"], data["y"], data["value"]
        )

    scan_presenter.scan_started.connect(on_scan_started_viz)
    scan_presenter.scan_progress.connect(on_scan_progress_viz)
    scan_presenter.field_scan_progress.connect(on_field_scan_progress_viz)
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
    
    # 11. Startup Sequence (hardware init if real hardware) or Direct Launch (if mocks only)
    # StartupView has been visible since the very start of main(); the log
    # panel it hosted moves into the Dashboard once it's shown.
    def on_startup_finished(success: bool, errors: list):
        if success:
            print("Hardware initialization successful.")
            startup_view.close()

            print("\n--- Launching Dashboard ---")
            dashboard.show()
            print("Dashboard launched successfully!")
        else:
            print(f"CRITICAL: Hardware initialization failed: {errors}")
            # StartupView will display the error
            # User can close the window manually

    lifecycle_presenter.startup_finished.connect(on_startup_finished)

    if use_startup:
        startup_view.set_phase("Initialisation matérielle...")
        app.processEvents()
        startup_view.start_hardware_init()
    else:
        # No hardware lifecycle to run for mocks - finish immediately
        on_startup_finished(success=True, errors=[])

    sys.exit(app.exec())


if __name__ == "__main__":
    main()