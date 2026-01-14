"""
Test Arcus Hardware Directly in Steps/Increments
Tests hardware communication without unit conversion (mm/µm).
Works directly with the controller in steps/increments.
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

def wait_for_user(prompt: str):
    print(f"\n>>> USER ACTION REQUIRED: {prompt}")
    print(">>> Press ENTER to continue...", end='', flush=True)
    sys.stdin.readline()

def test_arcus_in_steps():
    print("=" * 60)
    print("  ARCUS HARDWARE TEST - STEPS/INCREMENTS MODE")
    print("=" * 60)
    print("This test works directly in steps/increments.")
    print("No unit conversion (mm/µm) is performed.")
    print("=" * 60)
    print("\n⚠️  IMPORTANT: If motor doesn't move after changing TB6600 DIP switches:")
    print("   1. Verify PMX-4EX-SA → TB6600 connections:")
    print("      - Pulse (PUL) wire connected")
    print("      - Direction (DIR) wire connected")
    print("      - Enable (ENA) wire connected and at 5V HIGH")
    print("   2. Check TB6600 power supply (24-48V DC)")
    print("   3. Verify TB6600 DIP switches configuration")
    print("   4. Check motor → TB6600 wiring (4 wires: A+, A-, B+, B-)")
    print("   5. TB6600 may need power cycle after DIP switch change")
    print("\n✅ WORKING CONFIGURATIONS (discovered):")
    print("   Configuration 1: SW2=ON, SW5=OFF (others OFF)")
    print("   Configuration 2: SW3=ON only (others OFF) ← CURRENT")
    print("   - CRITICAL: SW5=ON prevents movement!")
    print("   - SW5=OFF allows movement")
    print("   - Note: Position errors observed (~30-40 steps drift)")
    print("\n🔍 DIAGNOSTIC: If motor works with OLD config but not new:")
    print("   → Run: diagnose_tb6600_config.py")
    print("   → Check current setting (SW4-SW6)")
    print("   → SW5=ON may set current too high for your setup")
    print("=" * 60)

    # Find DLL path (relative to driver directory)
    # The test is in tests/harware_only/, need to go up to find driver directory
    test_file = Path(__file__).resolve()
    # Go up: tests/harware_only -> tests -> arcus_performax_4EX
    # test_file.parent.parent.parent is already arcus_performax_4EX directory
    driver_dir = test_file.parent.parent.parent
    dll_path = driver_dir / "DLL64"
    
    print(f"\n[DEBUG] Test file: {test_file}")
    print(f"[DEBUG] Driver dir: {driver_dir}")
    print(f"[DEBUG] DLL path: {dll_path}")
    
    if not dll_path.exists():
        print(f"\n[ERROR] DLL path not found: {dll_path}")
        print("Please ensure DLL64 folder exists in the arcus_performax_4EX directory")
        print(f"\n[DEBUG] Driver dir exists: {driver_dir.exists()}")
        if driver_dir.exists():
            print(f"[DEBUG] Contents of driver dir: {list(driver_dir.iterdir())}")
        return
    
    print(f"\n[DLL] Using DLL path: {dll_path}")

    # 1. Initialize Controller with DLL path
    print("\n[1] Initializing Arcus Controller...")
    controller = ArcusPerformax4EXController(dll_path=str(dll_path))
    
    try:
        # 2. Connect
        print("\n[2] Connecting to Hardware...")
        if not controller.connect():
            print("    -> Connection Failed!")
            return
        print("    -> Connected successfully!")
        
        # 3. Get initial position (in steps)
        print("\n[3] Reading Initial Position (in steps)...")
        pos_x = controller.get_position("x")
        pos_y = controller.get_position("y")
        print(f"    -> X Position: {pos_x} steps")
        print(f"    -> Y Position: {pos_y} steps")
        
        # 4. Check if homed
        print("\n[4] Checking Homing Status...")
        x_homed = controller.is_homed("x")
        y_homed = controller.is_homed("y")
        print(f"    -> X Homed: {x_homed}")
        print(f"    -> Y Homed: {y_homed}")
        
        # 4b. Configure speeds for homing (important for homing to work)
        print("\n[4b] Configuring speeds for homing...")
        # Conservative speeds for 1/32 microstepping
        controller.set_axis_params("x", ls=100, hs=2000, acc=300, dec=300)
        controller.set_axis_params("y", ls=100, hs=2000, acc=300, dec=300)
        print("    -> Speeds configured: HS=2000, LS=100, ACC=300, DEC=300")
        
        # Verify speeds
        x_params = controller.get_axis_params_dict("x")
        y_params = controller.get_axis_params_dict("y")
        print(f"    -> X params: {x_params}")
        print(f"    -> Y params: {y_params}")
        
        # 4c. Reset position reference before homing (optional but recommended)
        print("\n[4c] Resetting position reference...")
        try:
            controller.set_position_reference("x", 0)
            controller.set_position_reference("y", 0)
            print("    -> Position references reset to 0")
            # Verify position after reset
            pos_x = controller.get_position("x")
            pos_y = controller.get_position("y")
            print(f"    -> Positions after reset: X={pos_x}, Y={pos_y}")
        except Exception as e:
            print(f"    -> Warning: Could not reset position reference: {e}")
        
        # 4d. Force stop and wait for motors to be idle
        print("\n[4d] Forcing stop and waiting for motors to be idle...")
        controller.stop("x", immediate=True)
        controller.stop("y", immediate=True)
        time.sleep(0.5)
        
        # Wait until both axes are stopped
        max_wait = 5.0
        start_wait = time.time()
        while (controller.is_moving("x") or controller.is_moving("y")) and (time.time() - start_wait < max_wait):
            print("    -> Waiting for motors to stop...")
            time.sleep(0.5)
        
        x_moving = controller.is_moving("x")
        y_moving = controller.is_moving("y")
        print(f"    -> X moving: {x_moving}")
        print(f"    -> Y moving: {y_moving}")
        
        # 4e. Check motor enable status and errors (via direct stage access)
        print("\n[4e] Checking motor enable status and errors...")
        print("=" * 60)
        print("  CRITICAL: Since you changed the TB6600 driver DIP switches,")
        print("  verify hardware connections:")
        print("  1. PMX-4EX-SA → TB6600 connections:")
        print("     - Pulse (PUL) : 5V signal")
        print("     - Direction (DIR) : 5V signal")
        print("     - Enable (ENA) : 5V signal (MUST be HIGH to enable)")
        print("  2. TB6600 power supply: 24-48V DC")
        print("  3. TB6600 DIP switches: Check 1/32 microstepping setting")
        print("  4. Motor → TB6600: 4 wires (A+, A-, B+, B-)")
        print("=" * 60)
        try:
            # Access stage directly for detailed diagnostics
            stage = controller._stage
            if stage:
                x_enabled = stage.is_enabled("x")
                y_enabled = stage.is_enabled("y")
                print(f"\n    -> X enabled (PMX-4EX-SA): {x_enabled}")
                print(f"    -> Y enabled (PMX-4EX-SA): {y_enabled}")
                
                if not x_enabled or not y_enabled:
                    print(f"    -> ⚠️  WARNING: Axis not enabled in controller!")
                    print(f"    -> This means PMX-4EX-SA Enable output is OFF")
                    print(f"    -> TB6600 ENA pin needs 5V HIGH to enable motor")
                
                # Check for limit errors
                x_limit_error = stage.check_limit_error("x")
                y_limit_error = stage.check_limit_error("y")
                print(f"    -> X limit error: {x_limit_error if x_limit_error else 'None'}")
                print(f"    -> Y limit error: {y_limit_error if y_limit_error else 'None'}")
                
                # Get status
                x_status = stage.get_status("x")
                y_status = stage.get_status("y")
                print(f"    -> X status: {x_status}")
                print(f"    -> Y status: {y_status}")
                
                # Clear any limit errors
                if x_limit_error:
                    print("    -> Clearing X limit error...")
                    stage.clear_limit_error("x")
                if y_limit_error:
                    print("    -> Clearing Y limit error...")
                    stage.clear_limit_error("y")
                
                # Ensure motors are enabled
                if not x_enabled:
                    print("    -> Enabling X axis in controller...")
                    stage.enable_axis("x", enable=True)
                    time.sleep(0.2)
                    x_enabled_after = stage.is_enabled("x")
                    print(f"    -> X enabled after command: {x_enabled_after}")
                if not y_enabled:
                    print("    -> Enabling Y axis in controller...")
                    stage.enable_axis("y", enable=True)
                    time.sleep(0.2)
                    y_enabled_after = stage.is_enabled("y")
                    print(f"    -> Y enabled after command: {y_enabled_after}")
                
                # Final enable check
                print(f"\n    -> Final enable status:")
                print(f"       X: {stage.is_enabled('x')}")
                print(f"       Y: {stage.is_enabled('y')}")
        except Exception as e:
            print(f"    -> Warning: Could not check motor status: {e}")
            import traceback
            traceback.print_exc()
        
        # 4f. Test small movement before homing
        wait_for_user("Ready to TEST small movement (10 steps) on X axis?")
        print("    -> Testing small movement (10 steps) on X...")
        try:
            # Mark as homed temporarily to allow movement
            controller.set_homed("x", True)
            
            # Get initial position
            pos_before = controller.get_position("x")
            print(f"    -> X Position BEFORE move: {pos_before} steps")
            
            # Check if moving before command
            if controller.is_moving("x"):
                print("    -> Warning: X is already moving before command!")
            
            # Access stage directly to check pulse speed
            stage = controller._stage
            if stage:
                speed_before = stage.get_current_axis_speed("x")
                print(f"    -> X Current speed BEFORE command: {speed_before} Hz (should be 0)")
            
            # Check speed settings before movement
            if stage:
                x_params = controller.get_axis_params_dict("x")
                print(f"    -> X Speed params: HS={x_params['hs']}, LS={x_params['ls']}, ACC={x_params['acc']}, DEC={x_params['dec']}")
                # Also check global speed
                try:
                    global_speed = stage.get_global_speed()
                    axis_speed = stage.get_axis_speed("x")
                    print(f"    -> Global speed: {global_speed} Hz, X axis speed: {axis_speed} Hz")
                    if axis_speed == 0 and global_speed == 0:
                        print(f"    -> ⚠️  WARNING: Both speeds are 0! This will prevent movement!")
                except:
                    pass
            
            # Perform movement
            print("    -> Sending move_by(+10) command...")
            try:
                controller.move_by("x", 10)
            except Exception as e:
                print(f"    -> ERROR during move_by: {e}")
                import traceback
                traceback.print_exc()
                return
            
            # IMMEDIATELY check if pulses are being sent
            time.sleep(0.05)  # Very short delay
            if stage:
                speed_after = stage.get_current_axis_speed("x")
                print(f"    -> X Current speed AFTER command: {speed_after} Hz")
                if speed_after == 0:
                    print(f"    -> ⚠️  CRITICAL: No pulses being sent! Speed is 0 Hz")
                    print(f"    -> This means the controller is NOT generating pulses")
                    print(f"    -> Possible causes:")
                    print(f"       1. Controller requires REAL homing (not just flag)")
                    print(f"       2. Speed settings are 0 or invalid")
                    print(f"       3. Controller is in a mode that blocks pulses")
                    print(f"       4. Hardware connection issue (PMX-4EX-SA → TB6600)")
                else:
                    print(f"    -> ✓ Pulses are being sent ({speed_after} Hz)")
            
            # Check if movement started
            time.sleep(0.1)
            is_moving_after = controller.is_moving("x")
            print(f"    -> X is_moving after command: {is_moving_after}")
            
            # Monitor speed during movement
            if stage:
                print("    -> Monitoring speed during movement...")
                for i in range(5):
                    time.sleep(0.2)
                    current_speed = stage.get_current_axis_speed("x")
                    is_moving = controller.is_moving("x")
                    print(f"       [{i+1}] Speed: {current_speed} Hz, Moving: {is_moving}")
                    if not is_moving:
                        break
            
            # Wait for movement
            print("    -> Waiting for movement to complete...")
            controller.wait_move("x", timeout=5.0)
            
            pos_after = controller.get_position("x")
            actual_movement = pos_after - pos_before
            print(f"    -> X Position AFTER move: {pos_after} steps")
            print(f"    -> Expected movement: +10 steps")
            print(f"    -> Actual movement: {actual_movement} steps")
            
            if abs(actual_movement - 10) > 2:  # Allow 2 steps tolerance
                print(f"    -> ⚠️  WARNING: Movement mismatch! Expected +10, got {actual_movement}")
                print(f"    -> This indicates the motor may not be moving physically")
            else:
                print(f"    -> ✓ Movement OK")
            
            # Move back
            print("\n    -> Moving back (-10 steps)...")
            pos_before_return = controller.get_position("x")
            controller.move_by("x", -10)
            controller.wait_move("x", timeout=5.0)
            pos_after_return = controller.get_position("x")
            return_movement = pos_after_return - pos_before_return
            print(f"    -> Position before return: {pos_before_return} steps")
            print(f"    -> Position after return: {pos_after_return} steps")
            print(f"    -> Return movement: {return_movement} steps")
            
            if abs(return_movement - (-10)) > 2:
                print(f"    -> ⚠️  WARNING: Return movement mismatch! Expected -10, got {return_movement}")
            else:
                print(f"    -> ✓ Return movement OK")
            
            # Final check
            final_pos = controller.get_position("x")
            total_error = abs(final_pos - pos_before)
            print(f"\n    -> Final position: {final_pos} steps")
            print(f"    -> Total position error: {total_error} steps")
            
            if total_error > 5:
                print(f"    -> ⚠️  WARNING: Position did not return to start! Error: {total_error} steps")
                print(f"    -> This suggests the motor is NOT moving physically")
            else:
                print(f"    -> ✓ Position returned correctly")
            
            # CRITICAL: Test direct with stage (bypass wrapper)
            print("\n    -> Testing DIRECT stage command (bypassing wrapper)...")
            if stage:
                try:
                    # Try direct move_to command
                    direct_pos_before = stage.get_position("x")
                    print(f"    -> Direct position before: {direct_pos_before}")
                    print(f"    -> Sending direct move_to command...")
                    stage.move_to("x", direct_pos_before + 20)
                    time.sleep(0.1)
                    direct_speed = stage.get_current_axis_speed("x")
                    print(f"    -> Direct speed after command: {direct_speed} Hz")
                    if direct_speed > 0:
                        print(f"    -> ✓ Direct command generates pulses!")
                        stage.wait_move("x", timeout=5.0)
                        direct_pos_after = stage.get_position("x")
                        print(f"    -> Direct position after: {direct_pos_after}")
                    else:
                        print(f"    -> ⚠️  Direct command also fails - no pulses!")
                        print(f"    -> This suggests a hardware/configuration issue")
                        stage.stop("x", immediate=True)
                except Exception as e:
                    print(f"    -> Direct command error: {e}")
                    import traceback
                    traceback.print_exc()
            
            # CRITICAL: Test JOG mode (doesn't require homing)
            print("\n    -> Testing JOG mode (no homing required)...")
            wait_for_user("Ready to TEST JOG mode? (motor will move continuously until stopped)")
            if stage:
                try:
                    jog_pos_before = stage.get_position("x")
                    print(f"    -> Position before jog: {jog_pos_before}")
                    print(f"    -> Starting JOG in + direction...")
                    print(f"    -> Motor should move continuously - watch for physical movement!")
                    stage.jog("x", "+")
                    
                    # Monitor speed immediately
                    time.sleep(0.1)
                    jog_speed = stage.get_current_axis_speed("x")
                    print(f"    -> JOG speed after 0.1s: {jog_speed} Hz")
                    
                    if jog_speed > 0:
                        print(f"    -> ✓ JOG generates pulses! ({jog_speed} Hz)")
                        print(f"    -> Motor should be moving now - check physically!")
                        
                        # Let it run for 2 seconds
                        for i in range(10):
                            time.sleep(0.2)
                            current_speed = stage.get_current_axis_speed("x")
                            current_pos = stage.get_position("x")
                            print(f"       [{i+1}] Speed: {current_speed} Hz, Position: {current_pos}")
                            if current_speed == 0:
                                print(f"       -> JOG stopped unexpectedly")
                                break
                        
                        # Stop jog
                        print(f"    -> Stopping JOG...")
                        stage.stop("x", immediate=True)
                        time.sleep(0.2)
                        jog_pos_after = stage.get_position("x")
                        print(f"    -> Position after jog: {jog_pos_after}")
                        print(f"    -> Position change: {jog_pos_after - jog_pos_before} steps")
                    else:
                        print(f"    -> ⚠️  JOG also fails - no pulses generated!")
                        print(f"    -> This confirms: PMX-4EX-SA is NOT generating pulses")
                        print(f"    -> Possible causes:")
                        print(f"       1. Hardware connection issue (USB/RS-485)")
                        print(f"       2. Controller firmware issue")
                        print(f"       3. Controller requires specific initialization")
                        print(f"       4. Output enable not properly set")
                        stage.stop("x", immediate=True)
                except Exception as e:
                    print(f"    -> JOG command error: {e}")
                    import traceback
                    traceback.print_exc()
                    try:
                        stage.stop("x", immediate=True)
                    except:
                        pass
            
            # Reset homed status for real homing
            controller.set_homed("x", False)
        except Exception as e:
            print(f"    -> Test movement failed: {e}")
            print("    -> This might indicate a hardware issue")
            import traceback
            traceback.print_exc()
            # Continue anyway to try homing
        
        # 5. Home X axis
        wait_for_user("Ready to HOME X axis?")
        print("    -> Homing X axis...")
        try:
            # Stop X axis first to avoid PULSING error
            controller.stop("x", immediate=True)
            time.sleep(0.2)
            
            # Check if moving before homing
            if controller.is_moving("x"):
                print("    -> Warning: X axis still moving, waiting...")
                max_wait = 3.0
                start_wait = time.time()
                while controller.is_moving("x") and (time.time() - start_wait < max_wait):
                    time.sleep(0.2)
            
            print("    -> Starting homing command...")
            controller.home("x", blocking=True, timeout=120.0)
            print("    -> X axis homed successfully!")
        except Exception as e:
            print(f"    -> X homing failed: {e}")
            import traceback
            traceback.print_exc()
            return
        
        pos_x = controller.get_position("x")
        print(f"    -> X Position after home: {pos_x} steps")
        
        # 6. Home Y axis
        wait_for_user("Ready to HOME Y axis?")
        print("    -> Homing Y axis...")
        try:
            # Stop Y axis first to avoid PULSING error
            controller.stop("y", immediate=True)
            time.sleep(0.2)
            controller.home("y", blocking=True, timeout=120.0)
            print("    -> Y axis homed successfully!")
        except Exception as e:
            print(f"    -> Y homing failed: {e}")
            import traceback
            traceback.print_exc()
            return
        
        pos_y = controller.get_position("y")
        print(f"    -> Y Position after home: {pos_y} steps")
        
        # 7. Move X by small increment
        wait_for_user("Ready to MOVE X by 100 steps?")
        print("    -> Moving X by +100 steps...")
        controller.move_by("x", 100)
        controller.wait_move("x", timeout=10.0)
        pos_x = controller.get_position("x")
        print(f"    -> X Position: {pos_x} steps")
        
        # 8. Move X back
        wait_for_user("Ready to MOVE X back by -100 steps?")
        print("    -> Moving X by -100 steps...")
        controller.move_by("x", -100)
        controller.wait_move("x", timeout=10.0)
        pos_x = controller.get_position("x")
        print(f"    -> X Position: {pos_x} steps (should be near 0)")
        
        # 9. Move X to absolute position
        wait_for_user("Ready to MOVE X to absolute position 500 steps?")
        print("    -> Moving X to 500 steps...")
        controller.move_to("x", 500)
        controller.wait_move("x", timeout=10.0)
        pos_x = controller.get_position("x")
        print(f"    -> X Position: {pos_x} steps")
        
        # 10. Move X back to 0
        wait_for_user("Ready to MOVE X back to 0 steps?")
        print("    -> Moving X to 0 steps...")
        controller.move_to("x", 0)
        controller.wait_move("x", timeout=10.0)
        pos_x = controller.get_position("x")
        print(f"    -> X Position: {pos_x} steps")
        
        # 11. Test Y axis
        wait_for_user("Ready to MOVE Y by 200 steps?")
        print("    -> Moving Y by +200 steps...")
        controller.move_by("y", 200)
        controller.wait_move("y", timeout=10.0)
        pos_y = controller.get_position("y")
        print(f"    -> Y Position: {pos_y} steps")
        
        # 12. Move Y back
        wait_for_user("Ready to MOVE Y back by -200 steps?")
        print("    -> Moving Y by -200 steps...")
        controller.move_by("y", -200)
        controller.wait_move("y", timeout=10.0)
        pos_y = controller.get_position("y")
        print(f"    -> Y Position: {pos_y} steps (should be near 0)")
        
        # 13. Test with 1/32 microstepping resolution
        # With 1/32 pas: 6400 steps = 1 full rotation
        # Small movements: 10, 50, 100 steps
        wait_for_user("Ready to test SMALL movements (10, 50, 100 steps)?")
        print("\n    -> Testing small movements (1/32 microstepping)...")
        
        test_steps = [10, 50, 100]
        for steps in test_steps:
            print(f"\n    -> Moving X by +{steps} steps...")
            controller.move_by("x", steps)
            controller.wait_move("x", timeout=5.0)
            pos_x = controller.get_position("x")
            print(f"       X Position: {pos_x} steps")
            time.sleep(0.5)
        
        # Move back
        print("\n    -> Moving X back to 0...")
        controller.move_to("x", 0)
        controller.wait_move("x", timeout=10.0)
        pos_x = controller.get_position("x")
        print(f"       X Position: {pos_x} steps")
        
        print("\n" + "=" * 60)
        print("  TEST COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("\nFinal Positions:")
        pos_x = controller.get_position("x")
        pos_y = controller.get_position("y")
        print(f"  X: {pos_x} steps")
        print(f"  Y: {pos_y} steps")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        
        # Emergency stop
        try:
            print("\n[EMERGENCY] Stopping all axes...")
            controller.stop("x", immediate=True)
            controller.stop("y", immediate=True)
        except:
            pass
    
    finally:
        print("\n[Cleanup] Closing connection...")
        controller.disconnect()
        print("    -> Disconnected.")

if __name__ == "__main__":
    test_arcus_in_steps()