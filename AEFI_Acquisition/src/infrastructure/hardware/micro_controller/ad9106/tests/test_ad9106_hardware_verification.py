"""
Hardware Verification Script for AD9106
---------------------------------------
This script allows manual verification of the AD9106 hardware configuration
using the refactored AD9106Controller.

Usage:
    python src/infrastructure/hardware/micro_controller/ad9106/tests/test_ad9106_hardware_verification.py

Prerequisites:
    - MCU connected via Serial (default COM10)
    - Oscilloscope connected to DDS outputs
"""

import sys
import time
from pathlib import Path

# Add src to path
root_dir = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(root_dir / "src"))

from infrastructure.hardware.micro_controller.ad9106.ad9106_controller import AD9106Controller
from infrastructure.hardware.micro_controller.MCU_serial_communicator import MCU_SerialCommunicator

def main():
    print("=== AD9106 Hardware Verification ===")
    
    # 1. Connect
    print("\n1. Connecting to MCU...")
    try:
        communicator = MCU_SerialCommunicator()
        # Ensure connection (if not already open)
        if not communicator.ser or not communicator.ser.is_open:
            print("   Opening serial connection on COM10...")
            communicator.connect("COM10", 1500000)
        print("   ✅ Connected.")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return

    # 2. Initialize Controller
    print("\n2. Initializing Controller...")
    controller = AD9106Controller(communicator)
    
    # 3. Reset to Defaults
    print("\n3. Resetting to Default Config...")
    result = controller.init_default_config()
    if result.is_success:
        print("   ✅ Defaults applied (Freq=1kHz, Gains=0/10000, Modes=AC).")
    else:
        print(f"   ❌ Init failed: {result.error}")
        return

    # 4. Interactive Menu
    while True:
        print("\n--- Menu ---")
        print("1. Set Frequency to 1 kHz")
        print("2. Set Frequency to 5 kHz")
        print("3. Set Gain to 50% (2750) on DDS1 & DDS2")
        print("4. Set Gain to 0% (OFF) on DDS1 & DDS2")
        print("5. Set Mode X_DIR (DDS1=0°, DDS2=0°)")
        print("6. Set Mode Y_DIR (DDS1=0°, DDS2=180°)")
        print("7. Set Mode CIRCULAR+ (DDS1=0°, DDS2=90°)")
        print("q. Quit")
        
        choice = input("\nEnter choice: ")
        
        if choice == '1':
            print("   Setting 1 kHz...")
            res = controller.set_dds_frequency(1000.0)
            print_result(res)
            
        elif choice == '2':
            print("   Setting 5 kHz...")
            res = controller.set_dds_frequency(5000.0)
            print_result(res)
            
        elif choice == '3':
            print("   Setting Gain 50% (2750)...")
            res1 = controller.set_dds_gain(1, 2750)
            res2 = controller.set_dds_gain(2, 2750)
            print_result(res1, "DDS1")
            print_result(res2, "DDS2")
            
        elif choice == '4':
            print("   Setting Gain 0%...")
            res1 = controller.set_dds_gain(1, 0)
            res2 = controller.set_dds_gain(2, 0)
            print_result(res1, "DDS1")
            print_result(res2, "DDS2")
            
        elif choice == '5':
            print("   Setting X_DIR (0° / 0°)...")
            res1 = controller.set_dds_phase(1, 0)
            res2 = controller.set_dds_phase(2, 0)
            print_result(res1, "DDS1 Phase=0")
            print_result(res2, "DDS2 Phase=0")
            
        elif choice == '6':
            print("   Setting Y_DIR (0° / 180°)...")
            res1 = controller.set_dds_phase(1, 0)
            res2 = controller.set_dds_phase(2, 32768)
            print_result(res1, "DDS1 Phase=0")
            print_result(res2, "DDS2 Phase=32768")
            
        elif choice == '7':
            print("   Setting CIRCULAR+ (0° / 90°)...")
            res1 = controller.set_dds_phase(1, 0)
            res2 = controller.set_dds_phase(2, 16384)
            print_result(res1, "DDS1 Phase=0")
            print_result(res2, "DDS2 Phase=16384")
            
        elif choice.lower() == 'q':
            break
            
        # Small delay to ensure commands are processed
        time.sleep(0.1)

def print_result(result, prefix="Command"):
    if result.is_success:
        print(f"   ✅ {prefix}: Success")
    else:
        print(f"   ❌ {prefix}: Failed - {result.error}")

if __name__ == "__main__":
    main()
