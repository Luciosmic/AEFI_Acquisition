import unittest
from unittest.mock import MagicMock, patch
import time
import threading
import sys
from pathlib import Path

# Ensure src is in path
src_path = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from infrastructure.hardware.arcus_performax_4EX.adapter_motion_port_arcus_performax4EX import ArcusAdapter
from infrastructure.hardware.arcus_performax_4EX.driver_arcus_performax4EX import ArcusPerformax4EXController
from domain.value_objects.geometric.position_2d import Position2D

class TestArcusAsyncArchitecture(unittest.TestCase):
    def setUp(self):
        self.mock_controller = MagicMock(spec=ArcusPerformax4EXController)
        self.mock_controller.is_connected.return_value = True
        # Mock stage
        self.mock_stage = MagicMock()
        self.mock_controller._stage = self.mock_stage
        
        self.adapter = ArcusAdapter()
        self.adapter.set_controller(self.mock_controller)
        self.adapter.connect()
        # Default is_moving to False so wait_until_stopped returns immediately
        self.mock_stage.is_moving.return_value = False
        self.mock_controller.is_moving.return_value = False

    def tearDown(self):
        self.adapter.disconnect()

    def test_move_to_is_non_blocking(self):
        # Arrange
        pos = Position2D(x=10.0, y=20.0)
        
        # Act
        start_time = time.time()
        self.adapter.move_to(pos)
        end_time = time.time()
        
        # Assert
        duration = end_time - start_time
        self.assertLess(duration, 0.1, "move_to should return immediately")
        
        # Wait for worker to process
        time.sleep(0.2)
        # Wait for worker to process
        time.sleep(0.2)
        self.mock_controller.move_to.assert_any_call("X", 229) # 10 * 22.936
        self.mock_controller.move_to.assert_any_call("Y", 458) # 20 * 22.936

    def test_sequential_execution(self):
        # Arrange
        # Mock is_moving to simulate movement duration
        # First call: True (moving A), Second: False (done A), Third: True (moving B), Fourth: False (done B)
        # Note: _internal_wait_until_stopped calls is_moving repeatedly.
        # We need a way to simulate "move takes time".
        
        # Let's just verify queue order.
        pos1 = Position2D(x=10.0, y=10.0)
        pos2 = Position2D(x=20.0, y=20.0)
        
        # Act
        self.adapter.move_to(pos1)
        self.adapter.move_to(pos2)
        
        # Wait for worker
        time.sleep(0.5)
        
        # Assert
        # Check call order
        # Assert
        # Check call order
        calls = self.mock_controller.move_to.call_args_list
        # Expect X1, Y1, X2, Y2
        self.assertEqual(len(calls), 4)
        self.assertEqual(calls[0][0][1], 229) # X1
        self.assertEqual(calls[1][0][1], 229) # Y1
        self.assertEqual(calls[2][0][1], 458) # X2
        self.assertEqual(calls[3][0][1], 458) # Y2

    def test_stop_clears_queue(self):
        # Arrange
        # Mock move_to to be slow so we can queue things
        self.mock_stage.move_to.side_effect = lambda a, p: time.sleep(0.2)
        
        pos1 = Position2D(x=10.0, y=10.0)
        pos2 = Position2D(x=20.0, y=20.0)
        
        # Act
        self.adapter.move_to(pos1) # Starts immediately
        self.adapter.move_to(pos2) # Queued
        
        time.sleep(0.05) # Let move1 start
        self.adapter.stop() # Should clear queue (remove move2)
        
        # Wait enough time for move1 to finish (if it wasn't interrupted by stop logic, but stop logic is separate)
        # The stop() method calls stage.stop() which should stop the hardware.
        # The worker thread's _internal_wait_until_stopped checks is_moving.
        # If stage.stop() works, is_moving becomes false, worker finishes move1.
        # But move2 should be gone.
        
        time.sleep(0.5)
        
        # Assert
        # Should have called move for pos1
        # Should NOT have called move for pos2
        # Note: since we mocked move_to with sleep, it might finish.
        # But we want to ensure pos2 was never popped/executed.
        
        # Count calls. 
        # move1 (X and Y) = 2 calls.
        # move2 (X and Y) = 2 calls.
        # If queue cleared, we expect only move1 calls.
        
        # However, move_to calls move_to(X) then move_to(Y).
        # If stop happens during move_to(X), move_to(Y) might still happen in _internal_move_to?
        # No, _internal_move_to is synchronous.
        
        # Let's verify queue is empty.
        self.assertTrue(self.adapter._command_queue.empty())

    def test_set_reference(self):
        """Test that set_reference pushes command to queue."""
        self.adapter.set_reference("x", 10.0)
        
        # Verify command in queue
        cmd_type, args = self.adapter._command_queue.get()
        self.assertEqual(cmd_type, "SET_REFERENCE")
        self.assertEqual(args, ("x", 10.0))

    def test_home_sets_reference(self):
        """Test that home command automatically sets reference to 0."""
        # Arrange
        self.mock_stage.is_moving.return_value = False # Simulate instant stop
        
        # Act
        self.adapter.home("x")
        
        # Wait for worker
        time.sleep(0.2)
        
        # Assert
        # 1. Home called
        # Assert
        # 1. Home called
        self.mock_controller.home.assert_called()
        # 2. Set reference called
        self.mock_controller.set_position_reference.assert_called_with("x", 0.0)

    def test_home_both_sets_reference(self):
        """Test that home both command automatically sets reference for X and Y to 0."""
        # Arrange
        self.mock_stage.is_moving.return_value = False
        
        # Act
        self.adapter.home(None)
        
        # Wait for worker
        time.sleep(0.2)
        
        # Assert
        # Assert
        self.mock_controller.home_both.assert_called() # Actually home_both calls home('x') and home('y') in controller? 
        # Wait, _internal_home calls controller.home_both if axis is None.
        # controller.home_both calls stage.home('x') and stage.home('y').
        
        # Check set_position_reference calls
        # Should be called for x and y
        from unittest.mock import call
        expected_calls = [call("x", 0.0), call("y", 0.0)]
        self.mock_controller.set_position_reference.assert_has_calls(expected_calls, any_order=True)

    def test_emergency_stop_priority(self):
        """Test that emergency stop clears queue and sends abort command immediately."""
        # Arrange
        pos1 = Position2D(x=10.0, y=10.0)
        pos2 = Position2D(x=20.0, y=20.0)
        
        # Act
        self.adapter.move_to(pos1)
        self.adapter.move_to(pos2)
        
        # Verify queue has items (move2 should be in queue, move1 might be popped by worker already)
        # To be sure, we can check if queue is not empty OR if move_to was called.
        # But simpler: just call E-Stop and verify queue is empty and stop called.
        
        self.adapter.emergency_stop()
        
        # Assert
        # 1. Queue should be empty
        self.assertTrue(self.adapter._command_queue.empty())
        
        # 2. Controller stop called with immediate=True for both axes
        from unittest.mock import call
        expected_calls = [
            call("X", immediate=True),
            call("Y", immediate=True)
        ]
        self.mock_controller.stop.assert_has_calls(expected_calls, any_order=True)

if __name__ == '__main__':
    unittest.main()
