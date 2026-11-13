import unittest

from domain.shared_kernel.events.excitation_dds_link_changed.excitation_dds_link_changed import (
    ExcitationDdsLinkChanged,
)


class TestExcitationDdsLinkChanged(unittest.TestCase):
    def test_carries_linked_flag(self) -> None:
        event = ExcitationDdsLinkChanged(linked=True)
        self.assertTrue(event.linked)

    def test_is_frozen(self) -> None:
        event = ExcitationDdsLinkChanged(linked=False)
        with self.assertRaises(Exception):
            event.linked = True


if __name__ == "__main__":
    unittest.main()
