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
from infrastructure.events.event_audit_log import EventAuditLog
from infrastructure.execution.thread_pool_task_runner import ThreadPoolTaskRunner
from infrastructure.execution.event_bus_motion_synchronizer import EventBusMotionSynchronizer
from infrastructure.persistence.csv_scan_export_port import CsvScanExportPort
from infrastructure.persistence.hdf5_scan_export_port import Hdf5ScanExportPort
from infrastructure.persistence.acquisition_snapshot_reader import AcquisitionSnapshotReader
from infrastructure.post_processing.aefi_post_processor_port import AefiPostProcessorPort
from application.services.scan_export_service.scan_export_service import ScanExportService

# --- Adapters (Mocks) ---
from infrastructure.mocks.adapter_mock_excitation_aware_acquisition import ExcitationAwareAcquisitionPort
from infrastructure.execution.electric_field_probe_acquisition_executor import ElectricFieldProbeAcquisitionExecutor
from infrastructure.mocks.adapter_mock_i_hardware_initialization_port import MockHardwareInitializationPort
from infrastructure.hardware.narda_ep600.adapter_electric_field_probe_port import NardaEP601ProbeAdapter
from infrastructure.hardware.narda_ep600.fake.fake_electric_field_probe_adapter import FakeElectricFieldProbeAdapter

# --- "Mock" hardware modes reuse the REAL composition roots/adapters, only the
# transport is faked (see FakeMCUSerialCommunicator / FakeArcusPerformax4EXController
# intention.md) — Hardware Config, lifecycle, and event sync all behave like real hardware.
from infrastructure.hardware.arcus_performax_4EX.composition_root_arcus import ArcusCompositionRoot
from infrastructure.hardware.arcus_performax_4EX.fake.fake_arcus_performax4ex_controller import (
    FakeArcusPerformax4EXController,
)
from infrastructure.hardware.micro_controller.mcu_composition_root import MCUCompositionRoot
from infrastructure.hardware.micro_controller.fake.fake_mcu_serial_communicator import (
    FakeMCUSerialCommunicator,
)

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
from interface.presenters.aefi_continuous_reading_presenter import AefiContinuousReadingPresenter
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
    # "mock" builds the REAL composition root/adapters with a faked transport
    # (FakeMCUSerialCommunicator / FakeArcusPerformax4EXController) — not a
    # bare stub — so Hardware Config, lifecycle, and event sync all behave
    # like real hardware. Excitation/continuous always follow "aefi_device"
    # (same MCUCompositionRoot, real or simulated) — no separate entry.
    HARDWARE_CONFIG = {
        "motion": "real",        # "mock" | "real"
        "aefi_device": "real",   # "mock" | "real" — whole MCU stack (ADS131A04 acquisition + AD9106 excitation + lifecycle + continuous)
        "electric_field_probe": "real",  # "mock" | "real" — picks the adapter only, connection is manual (cf. panel)
    }
    NARDA_COM_PORT = "COM8"  # cf. config_templates/electric_field_probe_config.json
    print("--- Starting Interface V2 ---")
    print(f"Hardware Config: {HARDWARE_CONFIG}")
    
    # 3. Infrastructure Setup (Event Bus)
    event_bus = InMemoryEventBus()

    # 3bis. Event audit log — persists every domain event to JSONL, for later
    # traceability/audit (see _system/self/event_store.md).
    audit_log = EventAuditLog(repo_root / ".aefi_acquisition" / "logs" / "events")
    event_bus.subscribe("*", audit_log.record)

    # 4. Instantiate Adapters
    print("\n--- Initializing Hardware Adapters ---")
    motion_port = None
    base_acquisition_port = None
    excitation_port = None
    continuous_executor = None
    lifecycle_adapters = []
    
    # --- Motion (Arcus) ---
    # "mock" still builds a real ArcusCompositionRoot — just with a faked
    # controller instead of the real DLL/USB one — so Hardware Config, the
    # startup/shutdown lifecycle, and ArcusAdapter's real worker/monitor
    # threads all run identically to the real-hardware path.
    if HARDWARE_CONFIG["motion"] == "real":
        print("  [motion] -> real (ArcusCompositionRoot)")
        arcus_root = ArcusCompositionRoot(event_bus=event_bus)
    else:
        print("  [motion] -> mock (ArcusCompositionRoot, simulated controller)")
        arcus_root = ArcusCompositionRoot(event_bus=event_bus, controller=FakeArcusPerformax4EXController())
    motion_port = arcus_root.motion
    lifecycle_adapters.append(arcus_root.lifecycle)

    # --- Acquisition (ADS131) + Excitation (AD9106) + Continuous — all part of MCU ---
    # Same principle: "mock" builds a real MCUCompositionRoot with a faked
    # serial transport, so AD9106/ADS131 controllers, configurators (Hardware
    # Config entries), and the excitation frequency-sync event all behave
    # exactly like real hardware.
    if HARDWARE_CONFIG["aefi_device"] == "real":
        print("  [acquisition] -> real (MCUCompositionRoot)")
        mcu_root = MCUCompositionRoot(event_bus=event_bus)
    else:
        print("  [acquisition] -> mock (MCUCompositionRoot, simulated communicator)")
        mcu_root = MCUCompositionRoot(event_bus=event_bus, communicator=FakeMCUSerialCommunicator())

    base_acquisition_port = mcu_root.acquisition
    excitation_port = mcu_root.excitation
    continuous_executor = mcu_root.continuous
    lifecycle_adapters.append(mcu_root.lifecycle)
    print(f"  [excitation] -> {HARDWARE_CONFIG['aefi_device']} (from MCUCompositionRoot)")
    print(f"  [continuous] -> {HARDWARE_CONFIG['aefi_device']} (from MCUCompositionRoot)")

    # --- Wrap acquisition port with excitation-aware wrapper (only in mock mode) ---
    # This simulates the physical coupling between excitation and acquisition —
    # the fake serial transport itself only returns noise, it doesn't model this.
    # For real hardware, the coupling is physical and doesn't need simulation.
    if HARDWARE_CONFIG["aefi_device"] == "mock":
        # Field simulation (4-sphere point-charge model + 8mm cube sensor,
        # empty-bench baseline) loads its geometry/gain/orientation from
        # .aefi_acquisition/configs/aefi_device_config.json — including the
        # real measured sensor.calibration.sensor_to_lab_rotation, not an
        # arbitrary demo angle.
        acquisition_port = ExcitationAwareAcquisitionPort(
            base_acquisition_port=base_acquisition_port,
            excitation_port=excitation_port,
        )
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
    # Excitation Service
    excitation_service = ExcitationConfigurationService(excitation_port, event_bus)

    scan_service = ScanApplicationService(
        motion_port, continuous_service, event_bus,
        task_runner=task_runner,
        motion_sync=motion_sync,
        auxiliary_probes=[narda_channel],
        excitation_service=excitation_service,
    )

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
    
    # arcus_root/mcu_root always exist now (mock mode = same composition
    # roots, simulated transport) — Hardware Config lists everything either way.
    configurators.append(arcus_root.config)
    print("  [config] -> added Arcus configurator")

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
    # AefiContinuousReadingPresenter is View-Agnostic regarding instantiation, but needs wiring later.
    # SensorTransformationPresenter NEEDS the panel in constructor.
    print("\n--- Creating UI Presenters ---")
    
    motion_presenter = MotionPresenter(motion_control_service, event_bus)
    excitation_presenter = ExcitationPresenter(excitation_service, event_bus)
    
    # Continuous Presenter needs Transformation Service now
    aefi_continuous_reading_presenter = AefiContinuousReadingPresenter(continuous_service, event_bus, transformation_service)

    # Electric Field Probe Presenter
    electric_field_probe_presenter = ElectricFieldProbePresenter(electric_field_probe_service, event_bus)
    
    # Transformation Presenter needs Panel + Service
    transformation_presenter = SensorTransformationPresenter(dashboard.panels["transformation"], transformation_service)
    
    
    # Scan Presenter
    scan_presenter = ScanPresenter(scan_service, scan_export_service, event_bus)
    
    # Hardware Advanced Config Presenter
    hardware_config_presenter = HardwareAdvancedConfigPresenter(hardware_config_service, event_bus)
    
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
    excitation_presenter.excitation_updated.connect(excitation_panel.set_state)
    excitation_presenter.refresh_state()
    print("  [excitation] wired")
    
    # Continuous Acquisition Panel
    aefi_continuous_reading_panel = dashboard.panels["aefi_continuous_reading"]
    aefi_continuous_reading_panel.acquisition_start_requested.connect(aefi_continuous_reading_presenter.on_acquisition_start_requested)
    aefi_continuous_reading_panel.acquisition_stop_requested.connect(aefi_continuous_reading_presenter.on_acquisition_stop_requested)
    
    # Calibration & Transformation Wiring
    aefi_continuous_reading_panel.calibrate_noise_requested.connect(aefi_continuous_reading_presenter.calibrate_noise)
    aefi_continuous_reading_panel.calibrate_phase_requested.connect(aefi_continuous_reading_presenter.calibrate_phase)
    aefi_continuous_reading_panel.calibrate_primary_requested.connect(aefi_continuous_reading_presenter.calibrate_primary)
    aefi_continuous_reading_panel.reset_calibration_requested.connect(aefi_continuous_reading_presenter.reset_calibration)

    # Correction toggles (panel -> presenter)
    aefi_continuous_reading_panel.noise_toggled.connect(aefi_continuous_reading_presenter.on_noise_toggled)
    aefi_continuous_reading_panel.phase_toggled.connect(aefi_continuous_reading_presenter.on_phase_toggled)
    aefi_continuous_reading_panel.primary_toggled.connect(aefi_continuous_reading_presenter.on_primary_toggled)

    # Correction state feedback (presenter -> panel)
    aefi_continuous_reading_presenter.correction_states_updated.connect(aefi_continuous_reading_panel.update_correction_states)

    aefi_continuous_reading_panel.apply_rotation_toggled.connect(aefi_continuous_reading_presenter.on_rotation_toggled)
    
    aefi_continuous_reading_presenter.acquisition_started.connect(aefi_continuous_reading_panel.on_acquisition_started)
    aefi_continuous_reading_presenter.acquisition_stopped.connect(aefi_continuous_reading_panel.on_acquisition_stopped)
    aefi_continuous_reading_presenter.sample_acquired.connect(aefi_continuous_reading_panel.on_sample_acquired)
    aefi_continuous_reading_presenter.angles_updated.connect(aefi_continuous_reading_panel.update_angles_display)
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
    aefi_voltage_map_panel = dashboard.panels["aefi_voltage_map"]
    electric_field_map_panel = dashboard.panels["electric_field_map"]
    
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
        aefi_voltage_map_panel.initialize_scan(
            config["x_min"], config["x_max"], config["x_nb_points"],
            config["y_min"], config["y_max"], config["y_nb_points"]
        )
        # Channel set depends on the connected probe (mono/bi/tri-axial),
        # so it's left empty here and populated lazily from the first point.
        electric_field_map_panel.initialize_scan(
            config["x_min"], config["x_max"], config["x_nb_points"],
            config["y_min"], config["y_max"], config["y_nb_points"],
            channels=[]
        )

    def on_scan_progress_viz(current, total, data):
        # data has 'x', 'y', 'value'
        aefi_voltage_map_panel.update_data_point_from_position(
            data["x"], data["y"], data["value"]
        )

    def on_field_scan_progress_viz(current, total, data):
        electric_field_map_panel.update_data_point_from_position(
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