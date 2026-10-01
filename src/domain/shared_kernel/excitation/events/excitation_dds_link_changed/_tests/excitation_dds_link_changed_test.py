import sys
import unittest
from pathlib import Path

src_dir = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(src_dir))

from domain.shared_kernel.excitation.events.excitation_dds_link_changed.excitation_dds_link_changed import (
    ExcitationDdsLinkChanged,
)


class TestExcitationDdsLinkChanged(unittest.TestCase):
    def test_carries_linked_flag(self):
        event = ExcitationDdsLinkChanged(linked=True)
        self.assertTrue(event.linked)

    def test_is_frozen(self):
        event = ExcitationDdsLinkChanged(linked=False)
        with self.assertRaises(Exception):
            event.linked = True


if __name__ == "__main__":
    unittest.main()
