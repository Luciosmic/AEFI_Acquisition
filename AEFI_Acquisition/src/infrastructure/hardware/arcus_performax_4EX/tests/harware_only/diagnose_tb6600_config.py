"""
Diagnostic Test: TB6600 Configuration Comparison
Tests why 1/32 microstepping doesn't work vs old configuration.

This test helps identify:
- Speed limitations with 1/32 microstepping
- Pulse frequency issues
- Configuration problems
"""
import sys
import time
import os
from pathlib import Path

# Add src to sys.path
current_path = Path(__file__).resolve()
src_path = None
for parent in current_path.parents:
    if parent.name == 'src':
        src_path = parent
        break

if src_path:
    if str(src_path) not in sys.path:
        sys.path.append(str(src_path))
else:
    print("Error: Could not find 'src' directory")
    sys.exit(1)

from infrastructure.hardware.arcus_performax_4EX.driver_arcus_performax4EX import ArcusPerformax4EXController

def test_speed_limits():
    """Test different speeds to find limits with 1/32 microstepping."""
    print("=" * 70)
    print("  TB6600 CONFIGURATION DIAGNOSTIC")
    print("=" * 70)
    print("\nThis test helps identify why 1/32 microstepping doesn't work.")
    print("It tests different speeds to find if there's a speed limit issue.")
    print("=" * 70)
    
    # Find DLL path
    test_file = Path(__file__).resolve()
    driver_dir = test_file.parent.parent.parent
    dll_path = driver_dir / "DLL64"
    
    if not dll_path.exists():
        print(f"\n[ERROR] DLL path not found: {dll_path}")
        return
    
    print(f"\n[DLL] Using DLL path: {dll_path}")
    
    # Initialize controller
    print("\n[1] Initializing Arcus Controller...")
    controller = ArcusPerformax4EXController(dll_path=str(dll_path))
    
    try:
        # Connect
        print("\n[2] Connecting to Hardware...")
        if not controller.connect():
            print("    -> Connection Failed!")
            return
        print("    -> Connected successfully!")
        
        # Get stage for direct access
        stage = controller._stage
        if not stage:
            print("    -> ERROR: Stage not available")
            return
        
        # Enable axes
        stage.enable_axis("x", enable=True)
        stage.enable_axis("y", enable=True)
        time.sleep(0.2)
        
        print("\n[3] Current Configuration:")
        x_params = controller.get_axis_params_dict("x")
        print(f"    -> X Speed params: HS={x_params['hs']}, LS={x_params['ls']}, ACC={x_params['acc']}, DEC={x_params['dec']}")
        
        # Test speeds from very low to high
        test_speeds = [
            (50, "Very Low"),
            (100, "Low"),
            (200, "Low-Medium"),
            (500, "Medium"),
            (1000, "Medium-High"),
            (2000, "High (current)"),
            (5000, "Very High"),
        ]
        
        print("\n[4] Testing different speeds with JOG mode:")
        print("=" * 70)
        print("IMPORTANT: Watch for physical motor movement!")
        print("If motor moves at low speeds but not high speeds,")
        print("this indicates a pulse frequency limit with 1/32 microstepping.")
        print("=" * 70)
        
        input("\nPress ENTER to start speed tests...")
        
        for speed_hz, speed_name in test_speeds:
            print(f"\n--- Testing {speed_name} speed: {speed_hz} Hz ---")
            
            # Set speed
            controller.set_axis_params("x", hs=speed_hz, ls=speed_hz//2, acc=300, dec=300)
            time.sleep(0.2)
            
            # Verify speed
            actual_params = controller.get_axis_params_dict("x")
            print(f"    -> Speed set: HS={actual_params['hs']} Hz")
            
            # Get initial position
            pos_before = stage.get_position("x")
            print(f"    -> Position before: {pos_before}")
            
            # Start JOG
            print(f"    -> Starting JOG at {speed_hz} Hz...")
            stage.jog("x", "+")
            
            # Monitor for 1 second
            time.sleep(0.2)
            speed_actual = stage.get_current_axis_speed("x")
            print(f"    -> Actual pulse speed: {speed_actual} Hz")
            
            if speed_actual > 0:
                print(f"    -> ✓ Pulses generated!")
                
                # Monitor for 1 more second
                time.sleep(1.0)
                pos_after = stage.get_position("x")
                pos_change = pos_after - pos_before
                speed_during = stage.get_current_axis_speed("x")
                
                print(f"    -> Position after 1.2s: {pos_after}")
                print(f"    -> Position change: {pos_change} steps")
                print(f"    -> Speed during: {speed_during} Hz")
                
                if pos_change > 0:
                    print(f"    -> ✓ MOTOR IS MOVING at {speed_hz} Hz!")
                else:
                    print(f"    -> ⚠️  Position changed but motor may not be moving physically")
            else:
                print(f"    -> ⚠️  NO PULSES generated at {speed_hz} Hz")
            
            # Stop
            stage.stop("x", immediate=True)
            time.sleep(0.5)
            
            # Ask user if motor moved
            user_input = input(f"    -> Did motor move PHYSICALLY at {speed_hz} Hz? (y/n): ").strip().lower()
            if user_input == 'y':
                print(f"    -> ✓ CONFIRMED: Motor moves at {speed_hz} Hz")
            else:
                print(f"    -> ✗ Motor does NOT move at {speed_hz} Hz")
            
            input(f"    -> Press ENTER to continue to next speed test...")
        
        print("\n" + "=" * 70)
        print("  DIAGNOSTIC SUMMARY")
        print("=" * 70)
        print("\nBased on the tests above:")
        print("1. If motor moves at LOW speeds but not HIGH speeds:")
        print("   → TB6600 has a pulse frequency limit with 1/32 microstepping")
        print("   → Solution: Use lower speeds (e.g., HS < 1000 Hz)")
        print("\n2. If motor doesn't move at ANY speed:")
        print("   → Check DIP switch configuration")
        print("   → Verify TB6600 power supply")
        print("   → Check PMX-4EX-SA → TB6600 connections")
        print("\n3. If motor moves at all speeds:")
        print("   → Configuration is OK, problem is elsewhere")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n[Cleanup] Stopping motors and disconnecting...")
        try:
            controller.stop("x", immediate=True)
            controller.stop("y", immediate=True)
        except:
            pass
        controller.disconnect()
        print("    -> Disconnected.")

if __name__ == "__main__":
    test_speed_limits()

