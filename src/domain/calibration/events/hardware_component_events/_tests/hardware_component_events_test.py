import unittest
from uuid import uuid4

from domain.calibration.events.hardware_component_events.hardware_component_events import (
    HardwareComponentMounted,
)
from domain.calibration.value_objects.hardware_component_kind.hardware_component_kind import (
    HardwareComponentKind,
)


class TestHardwareComponentEvents(unittest.TestCase):
    def test_mounted_event_is_frozen(self):
        event = HardwareComponentMounted(kind=HardwareComponentKind.ADC, component_name="ADS131A04", mounting_id=uuid4())
        self.assertEqual(event.component_name, "ADS131A04")
        with self.assertRaises(Exception):
            event.component_name = "other"


if __name__ == "__main__":
    unittest.main()
