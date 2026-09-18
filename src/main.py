import logging
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
from application.services.synchronous_detection_service.synchronous_detection_service import SynchronousDetectionService
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
from infrastructure.persistence.calibration.hardware_signature_reader import HardwareSignatureReader
from infrastructure.persistence.calibration.real_synchronous_detection_phase_calibration_repository import (
    RealSynchronousDetectionPhaseCalibrationRepository,
)
from infrastructure.hardware.micro_controller.ad9106.adapter_synchronous_detection_ad9106 import (
    AdapterSynchronousDetectionAD9106,
)
from infrastructure.post_processing.aefi_post_processor_port import AefiPostProcessorPort
from application.services.scan_export_service.scan_export_service import ScanExportService

from infrastructure.execution.electric_field_probe_acquisition_executor import ElectricFieldProbeAcquisitionExecutor

# --- Hardware composition (motion + MCU + probe, real or mock per hardware_config) ---
from infrastructure.hardware.hardware_composition_root import HardwareCompositionRoot

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
from interface.shell.dashboard_wiring import wire_dashboard
from interface.widgets.panels.logs_panel import LogsPanel, install_console_capture
from interface.presenters.motion_presenter import MotionPresenter
from interface.presenters.excitation_presenter import ExcitationPresenter
from interface.presenters.synchronous_detection_presenter import SynchronousDetectionPresenter
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

logger = logging.getLogger(__name__)


def main(hardware_config: dict | None = None):
    """
    Main entry point for Interface V2.
    Composition root that builds the dependency graph.

    hardware_config defaults to all-"real" — this is the launcher that ships
    on main. For an all-mock dev launch, use main_mock.py instead of editing
    this default.
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
        logger.info(f"Configs initialisées depuis templates : {seeded}")

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
    if hardware_config is None:
        hardware_config = {
            "motion": "real",
            "aefi_device": "real",   # whole MCU stack (ADS131A04 acquisition + AD9106 excitation + lifecycle + continuous)
            "electric_field_probe": "real",  # picks the adapter only, connection is manual (cf. panel)
        }
    NARDA_COM_PORT = "COM8"  # cf. config_templates/electric_field_probe_config.json
    print("--- Starting Interface V2 ---")
    logger.info(f"Hardware config: {hardware_config}")
    
    # 3. Infrastructure Setup (Event Bus)
    event_bus = InMemoryEventBus()

    # 3bis. Event audit log — persists every domain event to JSONL, for later
    # traceability/audit (see _system/self/event_store.md).
    audit_log = EventAuditLog(repo_root / ".aefi_acquisition" / "logs" / "events")
    event_bus.subscribe("*", audit_log.record)

    # 4. Instantiate Adapters
    print("\n--- Initializing Hardware Adapters ---")
    hw = HardwareCompositionRoot(hardware_config, event_bus, NARDA_COM_PORT)

    # 5. Create Hardware Initialization Port
    if hw.lifecycle_adapters:
        from infrastructure.hardware.composite_hardware_initialization_port import CompositeHardwareInitializationPort
        init_port = CompositeHardwareInitializationPort(hw.lifecycle_adapters)
    else:
        from infrastructure.mocks.adapter_mock_i_hardware_initialization_port import MockHardwareInitializationPort
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
    continuous_service = AefiAcquisitionService(hw.continuous_executor, hw.acquisition_port)
    logger.info("Services -> AefiAcquisitionService created (continuous acquisition)")

    # Electric Field Probe Service
    # Same reasoning: built before ScanApplicationService, which subscribes
    # to its sample stream rather than pulling probe_port directly.
    electric_field_probe_executor = ElectricFieldProbeAcquisitionExecutor(event_bus)
    electric_field_probe_service = ElectricFieldProbeService(
        executor=electric_field_probe_executor,
        probe_port=hw.probe_port,
        event_bus=event_bus,
    )
    logger.info("Services -> ElectricFieldProbeService created")

    # Scan Application Service — auxiliary probes (currently: Narda EF probe)
    # are registered as blocking channels; see AuxiliaryProbeChannel for what
    # "blocking" means and make_electric_field_probe_channel for the Narda wiring.
    narda_channel = make_electric_field_probe_channel(
        probe_port=hw.probe_port,
        probe_service=electric_field_probe_service,
        event_bus=event_bus,
    )
    # Excitation Service
    excitation_service = ExcitationConfigurationService(hw.excitation_port, event_bus)
    logger.info("Services -> ExcitationConfigurationService created")

    # Synchronous Detection Service (DDS3/DDS1 phase calibration)
    synchronous_detection_hardware_port = AdapterSynchronousDetectionAD9106(
        hw.mcu_root.ad9106_controller, hw.mcu_root.ad9106_configurator
    )
    hardware_signature = HardwareSignatureReader().read()
    synchronous_detection_calibration_repository = RealSynchronousDetectionPhaseCalibrationRepository()
    synchronous_detection_service = SynchronousDetectionService(
        hardware_port=synchronous_detection_hardware_port,
        calibration_repository=synchronous_detection_calibration_repository,
        hardware_signature=hardware_signature,
        event_bus=event_bus,
    )
    logger.info("Services -> SynchronousDetectionService created (signature=%s)", hardware_signature)

    scan_service = ScanApplicationService(
        hw.motion_port, continuous_service, event_bus,
        task_runner=task_runner,
        motion_sync=motion_sync,
        auxiliary_probes=[narda_channel],
        excitation_service=excitation_service,
    )
    logger.info("Services -> ScanApplicationService created (auxiliary_probes=1)")

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
    logger.info("Services -> ScanExportService created")

    # Motion Control Service
    motion_control_service = MotionControlService(hw.motion_port, event_bus)
    logger.info("Services -> MotionControlService created")

    # Transformation Service (Shared State)
    transformation_service = TransformationService(event_bus)

    # Hardware Configuration Service
    print("\n--- Creating Hardware Configuration Service ---")
    configurators: list[IHardwareAdvancedConfigurator] = []
    
    # hw.arcus_root/hw.mcu_root always exist now (mock mode = same composition
    # roots, simulated transport) — Hardware Config lists everything either way.
    configurators.append(hw.arcus_root.config)
    logger.info("Config -> added Arcus configurator")

    configurators.extend(hw.mcu_root.configurators)
    logger.info(f"Config -> added {len(hw.mcu_root.configurators)} MCU configurator(s)")

    hardware_config_service = HardwareConfigurationService(configurators)
    logger.info(f"Config -> service created with {len(configurators)} configurator(s)")

    # 7. Create Lifecycle Services (only if real hardware is used)
    # For mock-only, we skip startup
    use_startup = len(hw.lifecycle_adapters) > 0
    
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
    synchronous_detection_presenter = SynchronousDetectionPresenter(synchronous_detection_service, event_bus)

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
    wire_dashboard(
        dashboard,
        motion_presenter,
        excitation_presenter,
        synchronous_detection_presenter,
        aefi_continuous_reading_presenter,
        electric_field_probe_presenter,
        scan_presenter,
        hardware_config_presenter,
    )
    logger.debug("Transformation panel wired (via constructor)")

    # 11. Startup Sequence (hardware init if real hardware) or Direct Launch (if mocks only)
    # StartupView has been visible since the very start of main(); the log
    # panel it hosted moves into the Dashboard once it's shown.
    def on_startup_finished(success: bool, errors: list):
        if success:
            logger.info("Hardware initialization successful.")
            motion_presenter.on_speed_mode_requested(dashboard.panels["motion"].get_current_speed_mode())
            startup_view.close()

            print("\n--- Launching Dashboard ---")
            dashboard.show()
            logger.info("Dashboard launched successfully.")
        else:
            logger.error(f"Hardware initialization failed: {errors}")
            # StartupView will display the error
            # User can close the window manually

    lifecycle_presenter.startup_finished.connect(on_startup_finished)

    if use_startup:
        startup_view.set_phase("Initialisation matérielle...")
        app.processEvents()
        startup_view.start_hardware_init()
    else:
        # No hardware lifecycle to run for mocks - finish immediately
        logger.info("No real hardware in lifecycle (mock-only) — skipping startup sequence.")
        on_startup_finished(success=True, errors=[])

    sys.exit(app.exec())


if __name__ == "__main__":
    main()