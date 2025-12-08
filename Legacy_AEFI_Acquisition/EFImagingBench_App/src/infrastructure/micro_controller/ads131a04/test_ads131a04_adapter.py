"""
Test ADS131A04 Adapter with real hardware.

Usage:
    python test_ads131a04_adapter.py
"""

import sys
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(src_dir))

from ..MCU_serial_communicator import MCU_SerialCommunicator
from .ads131a04_adapter import ADS131A04Adapter
from ....domain.value_objects.measurement_uncertainty import MeasurementUncertainty


def test_connection():
    """Test 1: Connection to MCU"""
    print("\n=== Test 1: Connection ===")
    
    serial = MCU_SerialCommunicator()
    
    # TODO: Update with your COM port
    port = input("Enter COM port (e.g., COM3): ").strip()
    
    # Use correct baudrate for MCU (1.5 Mbaud)
    success = serial.connect(port, baudrate=1500000)
    
    if success:
        print("[OK] Connected successfully")
        return serial
    else:
        print("[FAIL] Connection failed")
        return None


def test_mcu_initialization(serial):
    """Test 2: Initialize MCU with default config"""
    print("\n=== Test 2: MCU Initialization ===")
    
    # Initialize ADC with default values (from old working code)
    print("  Configuring ADC registers...")
    
    # CLKIN divider ratio = 2
    serial.send_command("a13")
    serial.send_command("d2")
    
    # ICLK divider + Oversampling (address 14, combined value 32 for OSR=32, ICLK=2)
    serial.send_command("a14")
    serial.send_command("d32")
    
    # ADC Gains = 0 (gain of 1) for all channels
    for addr in [17, 18, 19, 20]:
        serial.send_command(f"a{addr}")
        serial.send_command("d0")
    
    print("[OK] MCU initialized")
    return True


def test_adapter_creation(serial):
    """Test 3: Create adapter"""
    print("\n=== Test 3: Adapter Creation ===")
    
    adapter = ADS131A04Adapter(serial)
    print("[OK] Adapter created")
    
    # Check initial state
    is_ready = adapter.is_ready()
    print(f"  Ready: {is_ready} (expected: False before configuration)")
    
    return adapter


def test_configuration(adapter):
    """Test 4: Configure for uncertainty"""
    print("\n=== Test 4: Configuration ===")
    
    # Create target uncertainty (example: 1 mV)
    uncertainty = MeasurementUncertainty(
        max_uncertainty_volts=0.001  # 1 mV
    )
    
    print(f"  Target uncertainty: {uncertainty.max_uncertainty_volts*1000:.3f} mV")
    
    try:
        adapter.configure_for_uncertainty(uncertainty)
        print("[OK] Configuration applied")
        
        is_ready = adapter.is_ready()
        print(f"  Ready: {is_ready} (expected: True after configuration)")
        
        return True
    except Exception as e:
        print(f"[FAIL] Configuration failed: {e}")
        return False


def test_single_acquisition(adapter):
    """Test 5: Single sample acquisition"""
    print("\n=== Test 5: Single Acquisition ===")
    
    try:
        measurement = adapter.acquire_sample()
        
        print("[OK] Acquisition successful")
        print(f"  Timestamp: {measurement.timestamp}")
        print(f"  X in-phase:     {measurement.voltage_x_in_phase:.6f} V")
        print(f"  X quadrature:   {measurement.voltage_x_quadrature:.6f} V")
        print(f"  Y in-phase:     {measurement.voltage_y_in_phase:.6f} V")
        print(f"  Y quadrature:   {measurement.voltage_y_quadrature:.6f} V")
        print(f"  Z in-phase:     {measurement.voltage_z_in_phase:.6f} V")
        print(f"  Z quadrature:   {measurement.voltage_z_quadrature:.6f} V")
        
        if measurement.uncertainty_estimate_volts:
            print(f"  Uncertainty:    {measurement.uncertainty_estimate_volts*1000:.3f} mV")
        
        return True
    except Exception as e:
        print(f"[FAIL] Acquisition failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multiple_acquisitions(adapter, n=5):
    """Test 6: Multiple acquisitions"""
    print(f"\n=== Test 6: Multiple Acquisitions (n={n}) ===")
    
    import time
    
    success_count = 0
    
    for i in range(n):
        try:
            measurement = adapter.acquire_sample()
            success_count += 1
            print(f"  Sample {i+1}/{n}: X_I={measurement.voltage_x_in_phase:.6f} V")
            time.sleep(0.1)  # Small delay between acquisitions
        except Exception as e:
            print(f"  Sample {i+1}/{n}: Failed - {e}")
    
    print(f"[OK] Success rate: {success_count}/{n}")
    return success_count == n


def main():
    """Run all tests"""
    print("=" * 60)
    print("ADS131A04 Adapter Hardware Test")
    print("=" * 60)
    
    # Test 1: Connection
    serial = test_connection()
    if not serial:
        print("\n[FAIL] Tests aborted: No connection")
        return
    
    # Test 2: MCU initialization
    test_mcu_initialization(serial)
    
    # Test 3: Adapter creation
    adapter = test_adapter_creation(serial)
    
    # Test 4: Configuration
    config_ok = test_configuration(adapter)
    if not config_ok:
        print("\n[WARN] Configuration failed, but continuing tests...")
    
    # Test 5: Single acquisition
    single_ok = test_single_acquisition(adapter)
    
    if single_ok:
        # Test 6: Multiple acquisitions
        test_multiple_acquisitions(adapter, n=5)
    
    # Cleanup
    print("\n=== Cleanup ===")
    serial.disconnect()
    print("[OK] Disconnected")
    
    print("\n" + "=" * 60)
    print("Tests completed")
    print("=" * 60)


if __name__ == "__main__":
    main()

