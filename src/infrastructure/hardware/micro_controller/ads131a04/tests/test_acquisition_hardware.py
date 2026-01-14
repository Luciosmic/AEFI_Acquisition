import sys
import os
import time
import serial.tools.list_ports

from infrastructure.hardware.micro_controller.MCU_serial_communicator import MCU_SerialCommunicator
from infrastructure.hardware.micro_controller.ads131a04.adapter_i_acquistion_port_ads131a04 import ADS131A04Adapter
from domain.models.scan.value_objects.measurement_uncertainty import MeasurementUncertainty

# Add src to path so we can import modules
# Add src to path so we can import modules
# Assuming this file is in src/infrastructure/hardware/micro_controller/ads131a04/tests/
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../..'))

def list_serial_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

def main():
    # User provided configuration
    selected_port = "COM10"
    baudrate = 1500000
    
    print(f"Attempting to connect to {selected_port} at {baudrate} baud...")

    communicator = MCU_SerialCommunicator()
    if communicator.connect(selected_port, baudrate=baudrate):
        print(f"Connected to {selected_port}")
    else:
        print(f"Failed to connect to {selected_port}")
        return

    try:
        adapter = ADS131A04Adapter(communicator)
        
        # Configure (mock configuration for now as per adapter implementation)
        print("Configuring adapter...")
        uncertainty = MeasurementUncertainty(max_uncertainty_volts=0.001)
        adapter.configure_for_uncertainty(uncertainty)
        
        if adapter.is_ready():
            print("Adapter is ready.")
        else:
            print("Adapter is NOT ready.")
            return

        print("\nAcquiring sample...")
        try:
            measurement = adapter.acquire_sample()
            print("\n--- Measurement Result ---")
            print(f"Timestamp: {measurement.timestamp}")
            print(f"Ch1 (X In-Phase): {measurement.voltage_x_in_phase:.6f} V")
            print(f"Ch2 (X Quadrature): {measurement.voltage_x_quadrature:.6f} V")
            print(f"Ch3 (Y In-Phase): {measurement.voltage_y_in_phase:.6f} V")
            print(f"Ch4 (Y Quadrature): {measurement.voltage_y_quadrature:.6f} V")
            print(f"Ch5 (Z In-Phase): {measurement.voltage_z_in_phase:.6f} V")
            print(f"Ch6 (Z Quadrature): {measurement.voltage_z_quadrature:.6f} V")
            print(f"Uncertainty: ±{measurement.uncertainty_estimate_volts:.6f} V")
            print("--------------------------")
        except Exception as e:
            print(f"Error during acquisition: {e}")

    finally:
        print("\nDisconnecting...")
        communicator.disconnect()

if __name__ == "__main__":
    main()
