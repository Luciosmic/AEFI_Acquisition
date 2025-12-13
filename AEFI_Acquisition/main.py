import os
import sys
from pathlib import Path

# Force PyQtGraph to use PyQt6 to avoid ambiguity and QAction errors
os.environ["PYQTGRAPH_QT_LIB"] = "PyQt6"

# Add src to sys.path to allow imports from any location
root_dir = Path(__file__).parent.resolve()
src_dir = root_dir / "src"
sys.path.insert(0, str(src_dir))

from PyQt6 import QtWidgets, QtGui

# Monkey patch for pyqtgraph compatibility with PyQt6
if not hasattr(QtWidgets, 'QAction'):
    QtWidgets.QAction = QtGui.QAction
if not hasattr(QtWidgets, 'QActionGroup'):
    QtWidgets.QActionGroup = QtGui.QActionGroup
if not hasattr(QtWidgets, 'QFileSystemModel'):
    QtWidgets.QFileSystemModel = QtGui.QFileSystemModel
if not hasattr(QtWidgets, 'QShortcut'):
    QtWidgets.QShortcut = QtGui.QShortcut
if not hasattr(QtWidgets, 'QUndoCommand'):
    QtWidgets.QUndoCommand = QtGui.QUndoCommand
if not hasattr(QtWidgets, 'QUndoGroup'):
    QtWidgets.QUndoGroup = QtGui.QUndoGroup
if not hasattr(QtWidgets, 'QUndoStack'):
    QtWidgets.QUndoStack = QtGui.QUndoStack

from PyQt6 import QtOpenGLWidgets
if not hasattr(QtWidgets, 'QOpenGLWidget'):
    QtWidgets.QOpenGLWidget = QtOpenGLWidgets.QOpenGLWidget

from PyQt6.QtWidgets import QApplication

# --- Domain & Application Services ---
from application.services.scan_application_service.scan_application_service import ScanApplicationService
from application.services.scan_application_service.scan_export_service import ScanExportService
from application.services.system_lifecycle_service.system_lifecycle_service import (
    SystemStartupApplicationService, 
    SystemShutdownApplicationService,
    StartupConfig
)
from application.services.excitation_configuration_service.excitation_configuration_service import ExcitationConfigurationService
from application.services.continuous_acquisition_service.continuous_acquisition_service import ContinuousAcquisitionService
from application.services.motion_control_service.motion_control_service import MotionControlService
from application.services.hardware_configuration_service.hardware_configuration_service import HardwareConfigurationService
from application.services.hardware_configuration_service.i_hardware_advanced_configurator import IHardwareAdvancedConfigurator
from application.dtos.scan_dtos import ExportConfigDTO

# --- Infrastructure ---
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.execution.step_scan_executor import StepScanExecutor
from infrastructure.persistence.csv_scan_export_port import CsvScanExportPort
from infrastructure.persistence.hdf5_scan_export_port import Hdf5ScanExportPort

# --- Ports (Abstract) ---
from application.services.motion_control_service.i_motion_port import IMotionPort
from application.services.scan_application_service.i_acquisition_port import IAcquisitionPort
from application.services.system_lifecycle_service.i_hardware_initialization_port import IHardwareInitializationPort

# --- Adapters (Mocks) ---
from infrastructure.mocks.adapter_mock_i_motion_port import MockMotionPort
from infrastructure.mocks.adapter_mock_i_acquisition_port import RandomNoiseAcquisitionPort
from infrastructure.mocks.adapter_mock_i_hardware_initialization_port import MockHardwareInitializationPort
from infrastructure.mocks.adapter_mock_i_excitation_port import MockExcitationPort
from infrastructure.mocks.adapter_mock_i_continuous_acquisition_executor import MockContinuousAcquisitionExecutor

# --- Adapters (Real) ---
# Real hardware adapters are imported conditionally in main() based on USE_SIMULATION flag


# --- UI ---
from interface.shell.dashboard_window import DashBoard
from interface.ui_2d_scan.presenter_2d_scan import ScanPresenter
from interface.ui_excitation_configuration.presenter_excitation import ExcitationPresenter
from interface.ui_continuous_acquisition.presenter_continuous_acquisition import ContinuousAcquisitionPresenter
from interface.ui_system_lifecycle.presenter_system_lifecycle import SystemLifecyclePresenter
from interface.ui_system_lifecycle.view_startup import StartupView
from interface.ui_motion_control.presenter_motion_control import MotionControlPresenter
from interface.ui_hardware_advanced_configuration.presenter_generic_hardware_config import GenericHardwareConfigPresenter


# ============================================================================
# Hardware Adapter Factory Functions
# ============================================================================

# ============================================================================
# Hardware Adapter Factory Functions
# ============================================================================
# (Replaced by Composition Roots)


def main():
    """
    Main entry point (Composition Root).
    Constructs the dependency graph and launches the application.
    """
    # 1. Create QApplication (FIRST THING)
    app = QApplication(sys.argv)
    app.setApplicationName("EF Imaging Bench")

    # 2. Configuration: Hardware Adapter Registry
    # Simple dict-based configuration: port_name -> adapter_type ("mock" | "real")
    HARDWARE_CONFIG = {
        "motion": "real",        # "mock" | "real"
        "acquisition": "real",   # "mock" | "real"
        "excitation": "real",    # "mock" | "real"
        "continuous": "real",    # "mock" | "real"
    }
    
    print(f"--- Starting Application ---")
    print(f"Hardware Config: {HARDWARE_CONFIG}")
    
    # 3. Infrastructure Setup (Event Bus)
    event_bus = InMemoryEventBus()
    
    # 4. Instantiate Adapters
    print("\n--- Initializing Hardware Adapters ---")
    motion_port = None
    acquisition_port = None
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
        acquisition_port = mcu_root.acquisition
        lifecycle_adapters.append(mcu_root.lifecycle)
        continuous_executor = mcu_root.continuous
        
        # --- Excitation (AD9106 - part of MCU) ---
        if HARDWARE_CONFIG["excitation"] == "real":
            excitation_port = mcu_root.excitation
            print("  [excitation] -> real (from MCUCompositionRoot)")
    else:
        print("  [acquisition] -> mock")
        acquisition_port = RandomNoiseAcquisitionPort()

    # --- Excitation (Fallback / Mock) ---
    if HARDWARE_CONFIG["excitation"] == "real":
        # If we are here, it means we wanted real excitation but didn't get it from MCU (e.g. acquisition=mock)
        if excitation_port is None:
            print("  [excitation] -> WARNING: Cannot use real excitation without MCU (acquisition=real required)")
            print("  [excitation] -> Falling back to mock")
            excitation_port = MockExcitationPort()
    else:
        print("  [excitation] -> mock")
        excitation_port = MockExcitationPort()

    # --- Continuous Acquisition ---
    if HARDWARE_CONFIG["continuous"] == "real":
        print("  [continuous] -> real (Not Implemented)")
        # TODO: Real continuous
    else:
        print("  [continuous] -> mock")
        continuous_executor = MockContinuousAcquisitionExecutor(event_bus)
    
    # 5. Create Hardware Initialization Port
    if lifecycle_adapters:
        from infrastructure.hardware.composite_hardware_initialization_port import CompositeHardwareInitializationPort
        init_port = CompositeHardwareInitializationPort(lifecycle_adapters)
    else:
        init_port = MockHardwareInitializationPort()

    # 6. Create Hardware Configuration Service
    configurators: list[IHardwareAdvancedConfigurator] = []
    if HARDWARE_CONFIG["motion"] == "real" and 'arcus_root' in locals():
        configurators.append(arcus_root.config)
    if HARDWARE_CONFIG["acquisition"] == "real" and mcu_root:
        configurators.extend(mcu_root.configurators)
    
    hardware_config_service = HardwareConfigurationService(configurators)

    # 7. Create Lifecycle Service & Presenter
    lifecycle_presenter = SystemLifecyclePresenter()
    startup_service = SystemStartupApplicationService(
        hardware_initializer=init_port,
        calibration_service=None, 
        event_bus=event_bus,
        output_port=lifecycle_presenter
    )
    
    # 8. Create Application Services
    print("\n--- Creating Application Services ---")
    
    # Scan Executor (Infrastructure service)
    scan_executor = StepScanExecutor(motion_port, acquisition_port, event_bus)
    
    # Scan Application Service
    scan_service = ScanApplicationService(motion_port, acquisition_port, event_bus, scan_executor)

    # Scan Export Service
    csv_export_port = CsvScanExportPort()
    hdf5_export_port = Hdf5ScanExportPort()
    export_service = ScanExportService(event_bus, csv_export_port, hdf5_export_port)
    default_export_config = ExportConfigDTO(
        enabled=True,
        output_directory="",
        filename_base="scan",
        format="HDF5",
    )
    export_service.configure_export(default_export_config)
    
    # Excitation Service
    excitation_service = ExcitationConfigurationService(excitation_port)
    
    # Continuous Acquisition Service
    continuous_service = ContinuousAcquisitionService(continuous_executor, acquisition_port)
    
    # Motion Control Service
    motion_presenter = MotionControlPresenter()
    motion_presenter.set_event_bus(event_bus)
    motion_control_service = MotionControlService(motion_port, event_bus)
    motion_presenter.set_service(motion_control_service)
    
    # Shutdown Service
    shutdown_service = SystemShutdownApplicationService(
        scan_service=scan_service,
        acquisition_service=None,
        hardware_initializer=init_port,
        event_bus=event_bus,
        output_port=lifecycle_presenter
    )
    lifecycle_presenter.set_services(startup_service, shutdown_service)
    
    # 9. Create UI Presenters
    print("\n--- Creating UI Presenters ---")
    scan_presenter = ScanPresenter(scan_service, hardware_config_service, export_service)
    scan_service.set_output_port(scan_presenter)
    
    excitation_presenter = ExcitationPresenter(excitation_service)
    continuous_presenter = ContinuousAcquisitionPresenter(continuous_service, event_bus)
    
    # Advanced Config Presenter
    config_presenter = GenericHardwareConfigPresenter(hardware_config_service)
    
    # 10. Prepare Startup View
    startup_view = StartupView(lifecycle_presenter)
    
    # 11. Define Startup Completion Handler
    # We need to keep a reference to the dashboard window so it doesn't get garbage collected
    dashboard_window = None

    def on_startup_finished(success: bool, errors: list):
        nonlocal dashboard_window
        if success:
            print("Hardware initialization successful.")
            startup_view.close()
            
            # Create and Show Main Window
            print("\n--- Launching Dashboard ---")
            dashboard_window = DashBoard(
                scan_presenter, 
                excitation_presenter, 
                continuous_presenter, 
                lifecycle_presenter,
                motion_presenter,
                config_presenter
            )
            dashboard_window.show()
            
            # Start monitoring now that hardware is connected
            motion_presenter.start_monitoring()
        else:
            print(f"CRITICAL: Hardware initialization failed: {errors}")
            # StartupView will display the error. 
            # We could add a button in StartupView to exit, or exit here after a delay.
            # For now, let the user close the window.

    lifecycle_presenter.startup_finished.connect(on_startup_finished)
    
    # 12. Show Splash Screen and Start App
    startup_view.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
