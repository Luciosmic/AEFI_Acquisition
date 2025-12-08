"""
Test Arcus Adapter with real hardware.

Usage:
    python -m src.infrastructure.arcus_performax_4EX.adapter_arcus_performax4EX_test
"""

import sys
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_dir))

from infrastructure.arcus_performax_4EX.adapter_arcus_performax4EX import ArcusAdapter
from domain.value_objects.geometric.position_2d import Position2D


def test_connection():
    """Test 1: Connection to Arcus"""
    print("\n=== Test 1: Connection ===")
    
    adapter = ArcusAdapter()
    
    # TODO: Update with your COM port or leave None for auto-detect
    port = input("Enter COM port (or press Enter for auto-detect): ").strip()
    adapter._port = port if port else None
    
    success = adapter.connect()
    
    if success:
        print("[OK] Connected successfully")
        return adapter
    else:
        print("[FAIL] Connection failed")
        return None


def test_get_position(adapter):
    """Test 2: Get current position"""
    print("\n=== Test 2: Get Current Position ===")
    
    try:
        position = adapter.get_current_position()
        print(f"[OK] Current position: X={position.x}, Y={position.y}")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to get position: {e}")
        return False


def test_is_moving(adapter):
    """Test 3: Check motion status"""
    print("\n=== Test 3: Motion Status ===")
    
    try:
        moving = adapter.is_moving()
        print(f"[OK] Is moving: {moving}")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to check motion status: {e}")
        return False


def test_small_move(adapter):
    """Test 4: Small relative move"""
    print("\n=== Test 4: Small Move ===")
    
    try:
        # Get current position
        start_pos = adapter.get_current_position()
        print(f"  Start position: X={start_pos.x}, Y={start_pos.y}")
        
        # Move 100 steps in X (adjust based on your setup)
        target = Position2D(x=start_pos.x + 100, y=start_pos.y)
        print(f"  Moving to: X={target.x}, Y={target.y}")
        
        adapter.move_to(target)
        
        # Wait for motion to complete
        print("  Waiting for motion to complete...")
        adapter.wait_until_stopped(timeout=10.0)
        
        # Check final position
        final_pos = adapter.get_current_position()
        print(f"  Final position: X={final_pos.x}, Y={final_pos.y}")
        
        # Move back
        print("  Moving back to start...")
        adapter.move_to(start_pos)
        adapter.wait_until_stopped(timeout=10.0)
        
        print("[OK] Move test completed")
        return True
    except Exception as e:
        print(f"[FAIL] Move test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_stop(adapter):
    """Test 5: Emergency stop"""
    print("\n=== Test 5: Stop Command ===")
    
    try:
        adapter.stop(immediate=False)
        print("[OK] Stop command sent")
        return True
    except Exception as e:
        print(f"[FAIL] Stop failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Arcus Adapter Hardware Test")
    print("=" * 60)
    
    # Test 1: Connection
    adapter = test_connection()
    if not adapter:
        print("\n[FAIL] Tests aborted: No connection")
        return
    
    # Test 2: Get position
    test_get_position(adapter)
    
    # Test 3: Motion status
    test_is_moving(adapter)
    
    # Test 4: Small move (optional - user confirmation)
    do_move = input("\nPerform movement test? (y/n): ").strip().lower()
    if do_move == 'y':
        test_small_move(adapter)
    else:
        print("  [SKIP] Movement test skipped")
    
    # Test 5: Stop
    test_stop(adapter)
    
    # Cleanup
    print("\n=== Cleanup ===")
    adapter.disconnect()
    print("[OK] Disconnected")
    
    print("\n" + "=" * 60)
    print("Tests completed")
    print("=" * 60)


if __name__ == "__main__":
    main()

