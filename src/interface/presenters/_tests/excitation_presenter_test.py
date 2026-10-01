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


class TestExcitationPresenterControl(unittest.TestCase):
    """While a controller (scan, automatic calibration) owns the excitation,
    the panel shows it and hand changes are refused visibly."""

    def setUp(self):
        self.port = MagicMock(spec=IExcitationPort)
        self.event_bus = InMemoryEventBus()
        self.service = ExcitationConfigurationService(excitation_port=self.port, event_bus=self.event_bus)
        self.presenter = ExcitationPresenter(self.service, self.event_bus)
        self.controllers, self.errors, self.updates = [], [], []
        self.presenter.controller_changed.connect(self.controllers.append)
        self.presenter.excitation_error.connect(self.errors.append)
        self.presenter.excitation_updated.connect(lambda *args: self.updates.append(args))

    def test_taking_and_releasing_control_is_shown(self):
        self.service.take_control("scan")
        self.service.release_control("scan")
        self.assertEqual(self.controllers, ["scan", ""])

    def test_hand_change_while_controlled_is_refused_and_panel_resynced(self):
        self.service.take_control("scan")
        self.updates.clear()

        self.presenter.on_excitation_changed("Y_DIR", 90.0, 90.0, 1000.0)

        self.port.apply_excitation.assert_not_called()
        self.assertEqual(len(self.errors), 1)
        self.assertIn("scan", self.errors[0])
        self.assertEqual(len(self.updates), 1)
        self.assertEqual(self.updates[0][1], 0.0)  # the real (unchanged) level, not the refused 90%


if __name__ == "__main__":
    unittest.main()
