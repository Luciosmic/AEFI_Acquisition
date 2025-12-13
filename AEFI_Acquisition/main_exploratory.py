import os
import sys
# Force PyQtGraph to use PyQt6 to avoid ambiguity and QAction errors
os.environ["PYQTGRAPH_QT_LIB"] = "PyQt6"

from PyQt6 import QtWidgets, QtGui
# Monkey patch for pyqtgraph < 0.14 (or environment quirks)
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

import logging
from pathlib import Path

# Add src to sys.path
root_dir = Path(__file__).parent.resolve()
src_dir = root_dir / "src"
sys.path.insert(0, str(src_dir))

from PyQt6.QtWidgets import QApplication
from PyQt6 import QtGui, QtWidgets

# --- Imports from main.py (Copied for Composition Root) ---
from application.services.scan_application_service.scan_application_service import ScanApplicationService
from application.services.scan_application_service.scan_export_service import ScanExportService
from application.services.hardware_configuration_service.hardware_configuration_service import HardwareConfigurationService
from application.services.system_lifecycle_service.system_lifecycle_service import (
    SystemStartupApplicationService, 
    SystemShutdownApplicationService
)
from application.services.excitation_configuration_service.excitation_configuration_service import ExcitationConfigurationService
from application.services.continuous_acquisition_service.continuous_acquisition_service import ContinuousAcquisitionService
from application.services.motion_control_service.motion_control_service import MotionControlService
from application.dtos.scan_dtos import ExportConfigDTO

from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.execution.step_scan_executor import StepScanExecutor
from infrastructure.persistence.csv_scan_export_port import CsvScanExportPort
from infrastructure.persistence.hdf5_scan_export_port import Hdf5ScanExportPort

from infrastructure.mocks.adapter_mock_i_motion_port import MockMotionPort
from infrastructure.mocks.adapter_mock_i_acquisition_port import RandomNoiseAcquisitionPort
from infrastructure.mocks.adapter_mock_i_hardware_advanced_configurator import MockHardwareAdvancedConfigurator
from infrastructure.mocks.adapter_mock_i_hardware_initialization_port import MockHardwareInitializationPort
from infrastructure.mocks.adapter_mock_i_excitation_port import MockExcitationPort
from infrastructure.mocks.adapter_mock_i_continuous_acquisition_executor import MockContinuousAcquisitionExecutor

from interface.ui_2d_scan.presenter_2d_scan import ScanPresenter
from interface.ui_excitation_configuration.presenter_excitation import ExcitationPresenter
from interface.ui_continuous_acquisition.presenter_continuous_acquisition import ContinuousAcquisitionPresenter
from interface.ui_system_lifecycle.presenter_system_lifecycle import SystemLifecyclePresenter
from interface.ui_system_lifecycle.view_shutdown import ShutdownView
from interface.ui_system_lifecycle.view_startup import StartupView
from interface.ui_motion_control.presenter_motion_control import MotionControlPresenter
from interface.ui_hardware_advanced_configuration.presenter_generic_hardware_config import GenericHardwareConfigPresenter

# --- NEW IMPORT ---
from presentation.shell.main_window import MainWindow

def main():
    print("--- Starting Exploratory UI (src/presentation) ---")
    
    if not hasattr(QtWidgets, 'QAction'):
        QtWidgets.QAction = QtGui.QAction
    
    # 1. Setup Same Infrastructure (Mocked for now)
    event_bus = InMemoryEventBus()
    motion_port = MockMotionPort()
    acquisition_port = RandomNoiseAcquisitionPort()
    init_port = MockHardwareInitializationPort()
    excitation_port = MockExcitationPort()
    continuous_executor = MockContinuousAcquisitionExecutor(event_bus)
    mock_provider = MockHardwareAdvancedConfigurator("mock_hardware")
    config_providers = [mock_provider]

    # 2. Services
    hardware_config_service = HardwareConfigurationService(config_providers)
    scan_executor = StepScanExecutor(motion_port, acquisition_port, event_bus)
    scan_service = ScanApplicationService(motion_port, acquisition_port, event_bus, scan_executor)
    
    csv_export_port = CsvScanExportPort()
    hdf5_export_port = Hdf5ScanExportPort()
    export_service = ScanExportService(event_bus, csv_export_port, hdf5_export_port)
    default_export_config = ExportConfigDTO(enabled=True, output_directory="", filename_base="scan", format="HDF5")
    export_service.configure_export(default_export_config)
    
    excitation_service = ExcitationConfigurationService(excitation_port)
    continuous_service = ContinuousAcquisitionService(continuous_executor, acquisition_port)
    
    # 3. Presenters
    lifecycle_presenter = SystemLifecyclePresenter()
    motion_presenter = MotionControlPresenter()
    
    startup_service = SystemStartupApplicationService(init_port, None, event_bus, lifecycle_presenter)
    shutdown_service = SystemShutdownApplicationService(scan_service, None, init_port, event_bus, lifecycle_presenter)
    lifecycle_presenter.set_services(startup_service, shutdown_service)
    
    motion_control_service = MotionControlService(motion_port, motion_presenter)
    motion_presenter.set_service(motion_control_service)

    scan_presenter = ScanPresenter(scan_service, hardware_config_service, export_service)
    scan_service.set_output_port(scan_presenter)
    
    excitation_presenter = ExcitationPresenter(excitation_service)
    continuous_presenter = ContinuousAcquisitionPresenter(continuous_service, event_bus)
    hardware_config_presenter = GenericHardwareConfigPresenter(hardware_config_service)

    # 4. Launch App
    app = QApplication(sys.argv)
    
    print("Launching Exploratory Main Window...")
    window = MainWindow(
        scan_presenter, 
        excitation_presenter, 
        continuous_presenter, 
        lifecycle_presenter,
        hardware_config_presenter,
        motion_presenter
    )
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
