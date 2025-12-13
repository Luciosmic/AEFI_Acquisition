"""
Demo standalone pour l'acquisition continue.

Lance une petite application Qt avec :
- MockAcquisitionPort (signal synthétique)
- ContinuousAcquisitionExecutor + ContinuousAcquisitionService
- ContinuousAcquisitionPresenter
- ContinuousAcquisitionWidget (UI avec start/stop + graphe 6 canaux)
"""

import sys
from pathlib import Path

# Add 'src' directory to sys.path to ensure modules can be imported
# This file is in src/interface/ui_continuous_acquisition/
# We want to add src/ to the path.
current_dir = Path(__file__).resolve().parent
src_dir = current_dir.parent.parent
sys.path.append(str(src_dir))

from PyQt6.QtWidgets import QApplication

from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.tests.mock_ports import RandomNoiseAcquisitionPort
from infrastructure.hardware.micro_controller.MCU_serial_communicator import MCU_SerialCommunicator
from infrastructure.hardware.micro_controller.ads131a04.adapter_ads131a04 import ADS131A04Adapter
from domain.value_objects.measurement_uncertainty import MeasurementUncertainty
from infrastructure.execution.continuous_acquisition_executor import (
    ContinuousAcquisitionExecutor,
)

from application.continuous_acquisition_service.continuous_acquisition_service import (
    ContinuousAcquisitionService,
)

from interface.ui_continuous_acquisition.presenter_continuous_acquisition import (
    ContinuousAcquisitionPresenter,
)
from interface.ui_continuous_acquisition.widget_continuous_acquisition import (
    ContinuousAcquisitionWidget,
)


def main() -> None:
    app = QApplication(sys.argv)

    # Infrastructure : event bus + mock acquisition
    event_bus = InMemoryEventBus()
    # Hardware Setup
    # SERIAL_PORT = "COM10"
    
    # # 1. Initialize Serial Communicator (Singleton)
    # communicator = MCU_SerialCommunicator()
    # # Baudrate 1.5M pour ADS131A04
    # connected = communicator.connect(port=SERIAL_PORT, baudrate=1500000)
    # if not connected:
    #     print(f"WARNING: Could not connect to serial port {SERIAL_PORT}. Acquisition may fail.")
        
    # # 2. Initialize Adapter
    # real_acquisition = ADS131A04Adapter(serial_communicator=communicator)
    # 
    # # 3. Configure Adapter (Required for is_ready() -> True)
    # # Using a default uncertainty to trigger default configuration (Gain 8, OSR appropriate)
    # default_uncertainty = MeasurementUncertainty(max_uncertainty_volts=0.001) # 1mV target
    # real_acquisition.configure_for_uncertainty(default_uncertainty)

    # acquisition_port = real_acquisition
    mock_acquisition = RandomNoiseAcquisitionPort()
    acquisition_port = mock_acquisition

    # Executor + service
    executor = ContinuousAcquisitionExecutor(
        event_bus=event_bus,
    )
    service = ContinuousAcquisitionService(executor, acquisition_port)

    # Presenter
    presenter = ContinuousAcquisitionPresenter(
        service=service,
        event_bus=event_bus,
    )

    # UI widget
    widget = ContinuousAcquisitionWidget(presenter)
    widget.resize(900, 600)
    widget.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()


