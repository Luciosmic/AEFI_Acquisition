import itertools
import unittest
import time
import threading
from unittest.mock import MagicMock
import sys
import os

# Add src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from tool.diagram_friendly_test import DiagramFriendlyTest

from infrastructure.hardware.arcus_performax_4EX.adapter_motion_port_arcus_performax4EX import ArcusAdapter
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from domain.value_objects.geometric.position_2d import Position2D
from domain.events.motion_events import MotionCompleted

class TestArcusEventBus(DiagramFriendlyTest):
    def setUp(self):
        super().setUp()
        self.log_divider("Setup")
        
        # 1. Create Event Bus
        self.event_bus = InMemoryEventBus()
        self.log_interaction("Test", "CREATE", "EventBus", "Created InMemoryEventBus")
        
        # 2. Create Mock Controller
        self.mock_controller = MagicMock()
        self.mock_controller.is_connected.return_value = True
        
        # Simulate motion: is_moving returns True several times then always False.
        # Infinite iterator prevents StopIteration when monitor/worker threads poll concurrently.
        _is_moving_values = itertools.chain(itertools.repeat(True, 6), itertools.repeat(False))
        self.mock_controller.is_moving.side_effect = lambda axis: next(_is_moving_values)
        
        # Configure get_position to return target steps (simulating successful move)
        # Calibration loaded from arcus_default_config.json: 21.8 microns/step → 45.87 steps/mm
        steps_per_mm = 1000.0 / 21.8
        target_x_steps = int(10.0 * steps_per_mm)
        target_y_steps = int(20.0 * steps_per_mm)
        
        def get_position_side_effect(axis):
            if axis == "X": return target_x_steps
            if axis == "Y": return target_y_steps
            return 0
            
        self.mock_controller.get_position.side_effect = get_position_side_effect
        
        self.log_interaction("Test", "CREATE", "MockController", "Created mock Arcus controller")
        
        # 3. Create Adapter
        self.adapter = ArcusAdapter(event_bus=self.event_bus)
        self.adapter.set_controller(self.mock_controller)
        self.log_interaction("Test", "CREATE", "ArcusAdapter", "Created adapter with injected controller")
        
        # 4. Connect (Enable)
        self.adapter.enable()
        self.log_interaction("Test", "CALL", "ArcusAdapter", "enable()")

    def tearDown(self):
        self.adapter.disable()
        super().tearDown()

    def test_move_publishes_event(self):
        self.log_divider("Execution")
        
        # 1. Subscribe to event
        received_events = []
        def on_motion_completed(event):
            received_events.append(event)
            self.log_interaction("EventBus", "PUBLISH", "Test", "MotionCompleted received", data={"motion_id": event.motion_id})
            
        self.event_bus.subscribe("motioncompleted", on_motion_completed)
        self.log_interaction("Test", "SUBSCRIBE", "EventBus", "Subscribed to motioncompleted")
        
        # 2. Command Move
        target_pos = Position2D(10.0, 20.0)
        self.log_interaction("Test", "CALL", "ArcusAdapter", "move_to", data={"target": str(target_pos)})
        
        motion_id = self.adapter.move_to(target_pos)
        
        # 3. Wait for completion (Adapter uses a worker thread)
        # We wait for the event to arrive
        start_wait = time.time()
        while len(received_events) == 0:
            if time.time() - start_wait > 2.0:
                self.fail("Timed out waiting for MotionCompleted event")
            time.sleep(0.1)
            
        # 4. Verify
        event = received_events[0]
        self.log_interaction("Test", "ASSERT", "Event", "Event ID matches")
        self.assertEqual(event.motion_id, motion_id)
        
        # Check position with tolerance (due to step resolution)
        # 1 step is approx 0.0436 mm
        tolerance = 0.05 
        self.log_interaction("Test", "ASSERT", "Event", f"Position matches within {tolerance}mm")
        self.assertAlmostEqual(event.final_position.x, target_pos.x, delta=tolerance)
        self.assertAlmostEqual(event.final_position.y, target_pos.y, delta=tolerance)
        
        print(f"Verified MotionCompleted event for {motion_id}")

if __name__ == '__main__':
    unittest.main()
