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
from application.services.sensor_calibration_service.sensor_calibration_service import SensorCalibrationService
from application.services.acquisition_throughput_characterization_service.acquisition_throughput_characterization_service import (
    AcquisitionThroughputCharacterizationService,
)
from infrastructure.persistence.acquisition_throughput.csv_acquisition_throughput_export_port import (
    CsvAcquisitionThroughputExportPort,
)
from infrastructure.acquisition_conditions.acquisition_conditions_reader import AcquisitionConditionsReader
from infrastructure.hardware.serial_link.ftdi_usb_latency_timer_reader import FtdiUsbLatencyTimerReader
from infrastructure.provenance.git_software_provenance_reader import GitSoftwareProvenanceReader
from application.services.source_geometry_calibration_service.source_geometry_calibration_service import SourceGeometryCalibrationService
from application.services.hardware_component_service.hardware_component_service import HardwareComponentService
from application.services.event_log_maintenance_service.event_log_maintenance_service import EventLogMaintenanceService
from domain.calibration.calibration import Calibration
from application.services.aefi_acquisition_service.aefi_acquisition_service import AefiAcquisitionService
from application.services.motion_control_service.motion_control_service import MotionControlService
from application.services.electric_field_probe_service.electric_field_probe_service import ElectricFieldProbeService

# --- Infrastructure ---
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.events.event_audit_log import EventAuditLog
from infrastructure.events.file_event_log_storage import FileEventLogStorage
from infrastructure.execution.thread_pool_task_runner import ThreadPoolTaskRunner
from infrastructure.execution.event_bus_motion_synchronizer import EventBusMotionSynchronizer
from infrastructure.persistence.csv_scan_export_port import CsvScanExportPort
from infrastructure.persistence.hdf5_scan_export_port import Hdf5ScanExportPort
from infrastructure.persistence.acquisition_snapshot_reader import AcquisitionSnapshotReader
from infrastructure.persistence.calibration.hardware_signature_reader import HardwareSignatureReader
from infrastructure.persistence.calibration.geometric_configuration_reader import GeometricConfigurationReader
from infrastructure.persistence.calibration.ideal_sensor_rotation_reader import IdealSensorRotationReader
from infrastructure.persistence.calibration.real_synchronous_detection_phase_calibration_repository import (
    RealSynchronousDetectionPhaseCalibrationRepository,
)
from infrastructure.persistence.calibration.real_sensor_calibration_repository import (
    RealSensorCalibrationRepository,
)
from infrastructure.persistence.calibration.real_source_geometry_calibration_repository import (
    RealSourceGeometryCalibrationRepository,
)
from infrastructure.persistence.calibration.real_hardware_component_repository import RealHardwareComponentRepository
from infrastructure.hardware.micro_controller.ad9106.adapter_synchronous_detection_ad9106 import (
    AdapterSynchronousDetectionAD9106,
)
from infrastructure.post_processing.aefi_post_processor_port import AefiPostProcessorPort, rotation_origin
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
from interface.widgets.sensor_orientation_view.sensor_orientation_view import configure_qt_opengl
from interface.widgets.panels.logs_panel import LogsPanel, install_console_capture
from interface.presenters.motion_presenter import MotionPresenter
from interface.presenters.excitation_presenter import ExcitationPresenter
from interface.presenters.synchronous_detection_presenter import SynchronousDetectionPresenter
from interface.presenters.sensor_calibration_presenter import SensorCalibrationPresenter
from interface.presenters.acquisition_throughput_characterization_presenter import (
    AcquisitionThroughputCharacterizationPresenter,
)
from interface.presenters.source_geometry_calibration_presenter import SourceGeometryCalibrationPresenter
from interface.presenters.hardware_component_presenter import HardwareComponentPresenter
from interface.presenters.event_log_presenter import EventLogPresenter
from interface.presenters.adc_output_rate_characterization_presenter import AdcOutputRateCharacterizationPresenter
from application.services.adc_output_rate_characterization_service.adc_output_rate_characterization_service import (
    AdcOutputRateCharacterizationService,
)
from infrastructure.persistence.adc_output_rate.csv_adc_output_rate_export_port import CsvAdcOutputRateExportPort
from interface.presenters.aefi_continuous_reading_presenter import AefiContinuousReadingPresenter
from interface.presenters.electric_field_probe_presenter import ElectricFieldProbePresenter
from interface.presenters.scan_presenter import ScanPresenter

# --- Transformation Service ---
from application.services.transformation_service.transformation_service import TransformationService
from application.services.transformation_service.dtos.transformation_dtos import SetRotationAnglesDTO

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

    # 1. Create QApplication (GL setup first: the splash is a top-level window
    # created before the 3D sensor view of the calibration panel)
    configure_qt_opengl()
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
            "oscilloscope": "real",  # DSO-X 2014A on DRDY, opened only during an ODR measurement
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
    continuous_service = AefiAcquisitionService(hw.continuous_executor, hw.acquisition_port, event_bus)
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

    # Source Geometry Calibration Service (4-sphere caliper measurements) —
    # now the live source of geometric configuration; GeometricConfigurationReader
    # is only used below, once, to seed this registry's first entry from the
    # legacy device config JSON when it has never been recorded yet.
    source_geometry_calibration_repository = RealSourceGeometryCalibrationRepository()
    source_geometry_calibration_service = SourceGeometryCalibrationService(
        calibration_repository=source_geometry_calibration_repository,
        event_bus=event_bus,
    )
    if not source_geometry_calibration_repository.find_all():
        legacy_geometry = GeometricConfigurationReader().read()
        source_geometry_calibration_service.record_calibration(
            sphere_diameters_m=list(legacy_geometry.sphere_diameters_m),
            pairwise_distances_ext_m=list(legacy_geometry.pairwise_distances_ext_m),
        )
        logger.info(
            "SourceGeometryCalibrationService: seeded initial entry from legacy aefi_device_config.json"
        )
    source_geometry_entry_id = source_geometry_calibration_service.get_current_entry_id()
    logger.info("Services -> SourceGeometryCalibrationService created (current geometry entry=%s)", source_geometry_entry_id)

    # Hardware components (sensor, boards, signal generation chip, ADC,
    # microcontroller, motors): catalog of characterized components (unique
    # name + history, any quantity may be "not characterized") and the
    # component mounted per kind. The mounted sensor and boards make up the
    # hardware signature; the device config template (generic names) only
    # fills a kind nothing is mounted for yet — WARNING, incomplete config.
    hardware_component_repository = RealHardwareComponentRepository()
    hardware_component_service = HardwareComponentService(repository=hardware_component_repository, event_bus=event_bus)
    hardware_signature = Calibration.resolve_current_hardware_signature(
        HardwareSignatureReader().read(),
        hardware_component_service.get_mounted_component_name("conditioning_electronics_board"),
        hardware_component_service.get_mounted_component_name("excitation_electronics_board"),
        hardware_component_service.get_mounted_component_name("sensor"),
    )
    logger.info("Services -> HardwareComponentService created (hardware signature=%s)", hardware_signature)

    # Sensor Calibration Service (mounting angles P of the mounted sensor).
    # Each angle calibration references the sensor's current mounting and the
    # current source geometry entry. Also owns the active rotation applied to
    # sensor readings: latest calibration for that mounting + geometry, else
    # the ideal angles (sensor.calibration.sources_to_sensor_rotation of the
    # device config).
    sensor_calibration_repository = RealSensorCalibrationRepository()
    sensor_calibration_service = SensorCalibrationService(
        calibration_repository=sensor_calibration_repository,
        sensor_mounting_id=hardware_component_service.get_current_mounting_id("sensor"),
        source_geometry_entry_id=source_geometry_entry_id,
        default_angles=IdealSensorRotationReader().read(),
        event_bus=event_bus,
        # Automatic calibration: drives the excitation, reads the ADC stream.
        excitation_service=excitation_service,
        acquisition_service=continuous_service,
        task_runner=task_runner,
    )
    logger.info("Services -> SensorCalibrationService created (geometry entry=%s)", source_geometry_entry_id)

    # Synchronous Detection Service (DDS3/DDS1 phase calibration)
    synchronous_detection_hardware_port = AdapterSynchronousDetectionAD9106(
        hw.mcu_root.ad9106_controller, hw.mcu_root.ad9106_configurator
    )
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
    acquisition_snapshot_port = AcquisitionSnapshotReader(
        hardware_component_repository=hardware_component_repository,
        sensor_calibration_repository=sensor_calibration_repository,
        source_geometry_calibration_repository=source_geometry_calibration_repository,
    )
    active_rotation = sensor_calibration_service.get_active_rotation()
    post_processing_port = AefiPostProcessorPort(
        event_bus,
        initial_rotation_angles=(
            active_rotation.theta_x_degrees, active_rotation.theta_y_degrees, active_rotation.theta_z_degrees,
        ),
        initial_rotation_origin=rotation_origin(
            active_rotation.is_trial, active_rotation.is_calibrated, active_rotation.recorded_at
        ),
    )
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

    # Transformation Service — applies E_sources = P·E_sensor with the active
    # angles (trial, calibrated or ideal) to every sample; follows ActiveSensorRotationChanged afterwards.
    transformation_service = TransformationService(event_bus)
    active_rotation = sensor_calibration_service.get_active_rotation()
    transformation_service.set_rotation_angles(SetRotationAnglesDTO(
        theta_x=active_rotation.theta_x_degrees,
        theta_y=active_rotation.theta_y_degrees,
        theta_z=active_rotation.theta_z_degrees,
    ))
    logger.info(
        "Services -> TransformationService created (active rotation %s, is_calibrated=%s)",
        (active_rotation.theta_x_degrees, active_rotation.theta_y_degrees, active_rotation.theta_z_degrees),
        active_rotation.is_calibrated,
    )

    # Hardware Configuration Service
    print("\n--- Creating Hardware Configuration Service ---")
    configurators: list[IHardwareAdvancedConfigurator] = []
    
    # hw.arcus_root/hw.mcu_root always exist now (mock mode = same composition
    # roots, simulated transport) — Hardware Config lists everything either way.
    configurators.append(hw.arcus_root.config)
    logger.info("Config -> added Arcus configurator")

    configurators.extend(hw.mcu_root.configurators)
    logger.info(f"Config -> added {len(hw.mcu_root.configurators)} MCU configurator(s)")

    hardware_config_service = HardwareConfigurationService(configurators, event_bus)
    logger.info(f"Config -> service created with {len(configurators)} configurator(s)")

    # Throughput / noise vs MCU n_avg (microcontroller tab of the Calibration panel).
    # Holds the excitation, the acquisition stream and the n_avg / OSR configuration
    # (Hardware Advanced Config) while it runs.
    # Its acquisition-parameters.json records the conditions: catalog + resolved
    # chip configs (same snapshot as the scan export), controller memories,
    # active rotation, phase compensation, serial link, motors, real/mock backends.
    acquisition_conditions = AcquisitionConditionsReader(
        snapshot_reader=acquisition_snapshot_port,
        hardware_component_repository=hardware_component_repository,
        sensor_calibration_repository=sensor_calibration_repository,
        active_rotation=sensor_calibration_service.get_active_rotation,
        compensation_enabled=synchronous_detection_service.is_compensation_enabled,
        ad9106_memory_state=hw.mcu_root.ad9106_controller.get_memory_state,
        oversampling_ratio=hw.acquisition_averaging.get_oversampling_ratio,
        serial_communicator=hw.mcu_root.lifecycle.get_communicator(),
        motion_port=hw.motion_port,
        hardware_backends=hardware_config,
    )
    acquisition_throughput_service = AcquisitionThroughputCharacterizationService(
        excitation_service=excitation_service,
        acquisition_service=continuous_service,
        averaging_port=hw.acquisition_averaging,
        export_port=CsvAcquisitionThroughputExportPort(),
        task_runner=task_runner,
        event_bus=event_bus,
        hardware_configuration=hardware_config_service,
        conditions_port=acquisition_conditions,
        software_provenance_port=GitSoftwareProvenanceReader(),
        usb_latency_timer_port=FtdiUsbLatencyTimerReader(),
    )
    logger.info("Services -> AcquisitionThroughputCharacterizationService created")

    # ADC output data rate on DRDY (ADC tab of the Calibration panel): holds the
    # ads131a04 configuration and the acquisition stream while it runs.
    adc_output_rate_service = AdcOutputRateCharacterizationService(
        oversampling_port=hw.adc_oversampling,
        capture_port=hw.drdy_capture,
        export_port=CsvAdcOutputRateExportPort(),
        acquisition_service=continuous_service,
        hardware_configuration=hardware_config_service,
        task_runner=task_runner,
    )
    logger.info("Services -> AdcOutputRateCharacterizationService created")

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
    print("\n--- Creating UI Presenters ---")
    
    motion_presenter = MotionPresenter(motion_control_service, event_bus)
    excitation_presenter = ExcitationPresenter(excitation_service, event_bus)
    synchronous_detection_presenter = SynchronousDetectionPresenter(synchronous_detection_service, event_bus)
    sensor_calibration_presenter = SensorCalibrationPresenter(
        sensor_calibration_service, event_bus
    )
    source_geometry_calibration_presenter = SourceGeometryCalibrationPresenter(
        source_geometry_calibration_service, event_bus
    )
    hardware_component_presenters = [
        HardwareComponentPresenter(hardware_component_service, kind, event_bus)
        for kind in hardware_component_service.list_kinds()
    ]
    acquisition_throughput_presenter = AcquisitionThroughputCharacterizationPresenter(acquisition_throughput_service)
    adc_output_rate_presenter = AdcOutputRateCharacterizationPresenter(adc_output_rate_service)

    # Continuous Presenter needs Transformation Service now
    aefi_continuous_reading_presenter = AefiContinuousReadingPresenter(
        continuous_service, event_bus, transformation_service, export_service=scan_export_service
    )

    # Electric Field Probe Presenter
    electric_field_probe_presenter = ElectricFieldProbePresenter(electric_field_probe_service, event_bus)
    
    
    
    # Scan Presenter
    scan_presenter = ScanPresenter(scan_service, scan_export_service, event_bus)
    
    # Hardware Advanced Config Presenter
    hardware_config_presenter = HardwareAdvancedConfigPresenter(hardware_config_service, event_bus)

    # Event log maintenance — shown in the Logs panel, nothing deleted without the user
    event_log_presenter = EventLogPresenter(
        EventLogMaintenanceService(FileEventLogStorage(audit_log.path.parent, live_session=audit_log.path))
    )

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
        sensor_calibration_presenter,
        source_geometry_calibration_presenter,
        hardware_component_presenters,
        event_log_presenter,
        acquisition_throughput_presenter,
        adc_output_rate_presenter,
    )

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