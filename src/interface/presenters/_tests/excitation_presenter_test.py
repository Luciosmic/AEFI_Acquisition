"""Unit tests for ExcitationPresenter's DDS1/DDS2 link sync with the
Hardware Advanced Config tab (see excitation_presenter.py)."""

import unittest
from unittest.mock import MagicMock

from interface.presenters.excitation_presenter import ExcitationPresenter
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from application.services.excitation_configuration_service.excitation_configuration_service import (
    ExcitationConfigurationService,
    EXCITATION_DDS_LINK_CHANGED_TOPIC,
)
from application.services.excitation_configuration_service.ports.i_excitation_port import IExcitationPort
from domain.shared_kernel.excitation.events.excitation_dds_link_changed.excitation_dds_link_changed import (
    ExcitationDdsLinkChanged,
)


class TestExcitationPresenterLinkSync(unittest.TestCase):
    def setUp(self):
        self.port = MagicMock(spec=IExcitationPort)
        self.event_bus = InMemoryEventBus()
        self.service = ExcitationConfigurationService(excitation_port=self.port, event_bus=self.event_bus)
        self.presenter = ExcitationPresenter(self.service, self.event_bus)
        self.received_link_states = []
        self.presenter.link_state_changed.connect(self.received_link_states.append)

    def test_refresh_state_pushes_current_link_state(self):
        self.presenter.refresh_state()

        self.assertEqual(self.received_link_states, [True])  # default

    def test_hardware_advanced_link_toggle_refreshes_excitation_panel(self):
        self.event_bus.publish(EXCITATION_DDS_LINK_CHANGED_TOPIC, ExcitationDdsLinkChanged(linked=False))

        self.assertEqual(self.received_link_states, [False])

    def test_on_link_toggled_calls_service(self):
        self.presenter.on_link_toggled(False)

        self.port.set_link_dds1_dds2.assert_called_once_with(False)
        self.assertFalse(self.service.is_linked())


if __name__ == "__main__":
    unittest.main()
