"""EventBusMotionSynchronizer: a motion that ends before the wait registers
(null move) must not be missed."""

import threading
import unittest

from domain.shared_kernel.events.motion_completed.motion_completed import MotionCompleted
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.execution.event_bus_motion_synchronizer import EventBusMotionSynchronizer


def _completed(motion_id: str) -> MotionCompleted:
    return MotionCompleted(motion_id=motion_id, final_position=Position2D(x=0, y=0), duration_ms=0.0)


class TestEventBusMotionSynchronizer(unittest.TestCase):
    def setUp(self):
        self.event_bus = InMemoryEventBus()
        self.sync = EventBusMotionSynchronizer(self.event_bus)

    def test_completion_published_before_the_wait_is_not_missed(self):
        self.event_bus.publish("motioncompleted", _completed("m1"))
        self.assertTrue(self.sync.wait_for_motion("m1", timeout_seconds=0.5).is_success)

    def test_completion_published_during_the_wait_releases_it(self):
        threading.Timer(0.05, lambda: self.event_bus.publish("motioncompleted", _completed("m2"))).start()
        self.assertTrue(self.sync.wait_for_motion("m2", timeout_seconds=2.0).is_success)

    def test_another_motion_completion_does_not_release_the_wait(self):
        self.event_bus.publish("motioncompleted", _completed("other"))
        self.assertTrue(self.sync.wait_for_motion("m3", timeout_seconds=0.1).is_failure)

    def test_an_early_outcome_is_consumed_once(self):
        self.event_bus.publish("motioncompleted", _completed("m4"))
        self.sync.wait_for_motion("m4", timeout_seconds=0.5)
        self.assertTrue(self.sync.wait_for_motion("m4", timeout_seconds=0.1).is_failure)


if __name__ == "__main__":
    unittest.main()
