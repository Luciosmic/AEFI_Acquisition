"""
Unit tests for HardwareAdvancedConfigPresenter's frequency sync with the
Excitation panel (see hardware_advanced_config_presenter.py docstring).
"""

import unittest

from interface.presenters.hardware_advanced_config_presenter import HardwareAdvancedConfigPresenter
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from application.services.hardware_configuration_service.hardware_configuration_service import (
    HardwareConfigurationService,
)
from application.services.excitation_configuration_service.excitation_configuration_service import (
    EXCITATION_FREQUENCY_CHANGED_TOPIC,
)
from domain.shared_kernel.excitation.events.excitation_frequency_changed.excitation_frequency_changed import (
    ExcitationFrequencyChanged,
)
from domain.shared_kernel.excitation.events.dds_channel_config_changed.dds_channel_config_changed import (
    DdsChannelConfigChanged,
)
from interface.presenters.hardware_advanced_config_presenter import DDS_CHANNEL_CONFIG_CHANGED_TOPIC
from domain.shared_kernel.value_objects.hardware_configuration.hardware_advanced_parameter_schema import (
    NumberParameterSchema,
)


class FakeAD9106Configurator:
    """Duck-typed IHardwareAdvancedConfigurator — no hardware, no disk I/O."""

    hardware_id = "ad9106_dds"
    display_name = "AD9106 DDS"

    @staticmethod
    def get_parameter_specs():
        return [
            NumberParameterSchema(
                key="frequency_hz", display_name="Frequency", default_value=1000.0,
                min_value=0.1, max_value=8_000_000.0, unit="Hz", group="Global",
            ),
            NumberParameterSchema(
                key="ch1_gain", display_name="DDS 1 Gain", default_value=0.0,
                min_value=0.0, max_value=16376.0, group="DDS 1",
            ),
            NumberParameterSchema(
                key="ch1_phase", display_name="DDS 1 Phase", default_value=0.0,
                min_value=0.0, max_value=65535.0, group="DDS 1",
            ),
            NumberParameterSchema(
                key="ch2_gain", display_name="DDS 2 Gain", default_value=0.0,
                min_value=0.0, max_value=16376.0, group="DDS 2",
            ),
            NumberParameterSchema(
                key="ch2_phase", display_name="DDS 2 Phase", default_value=0.0,
                min_value=0.0, max_value=65535.0, group="DDS 2",
            ),
        ]

    def apply_config(self, config):
        pass

    def save_config_as_default(self, config):
        pass


class TestHardwareAdvancedConfigPresenterFrequencySync(unittest.TestCase):
    def setUp(self):
        self.event_bus = InMemoryEventBus()
        self.service = HardwareConfigurationService([FakeAD9106Configurator()])
        self.presenter = HardwareAdvancedConfigPresenter(self.service, self.event_bus)
        self.received = []
        self.presenter.specs_loaded.connect(lambda hw_id, specs: self.received.append((hw_id, specs)))

    def test_excitation_panel_frequency_change_refreshes_selected_ad9106_specs(self):
        self.presenter.select_hardware("ad9106_dds")
        self.received.clear()  # drop the select_hardware() emission itself

        self.event_bus.publish(
            EXCITATION_FREQUENCY_CHANGED_TOPIC, ExcitationFrequencyChanged(frequency_hz=2500.0)
        )

        self.assertEqual(len(self.received), 1)
        hw_id, specs = self.received[0]
        self.assertEqual(hw_id, "ad9106_dds")
        freq_spec = next(s for s in specs if s.key == "frequency_hz")
        self.assertEqual(freq_spec.default_value, 2500.0)
        # Other specs must survive untouched — a full re-fetch would revert
        # any unsaved edit and also re-read the (possibly stale) default file.
        gain_spec = next(s for s in specs if s.key == "ch1_gain")
        self.assertEqual(gain_spec.default_value, 0.0)

    def test_frequency_change_ignored_when_no_hardware_selected(self):
        self.event_bus.publish(
            EXCITATION_FREQUENCY_CHANGED_TOPIC, ExcitationFrequencyChanged(frequency_hz=2500.0)
        )
        self.assertEqual(self.received, [])

    def test_excitation_panel_level_change_refreshes_gain_and_phase_for_that_channel(self):
        self.presenter.select_hardware("ad9106_dds")
        self.received.clear()

        self.event_bus.publish(
            DDS_CHANNEL_CONFIG_CHANGED_TOPIC, DdsChannelConfigChanged(channel=2, gain=1650, phase=32768)
        )

        self.assertEqual(len(self.received), 1)
        hw_id, specs = self.received[0]
        self.assertEqual(hw_id, "ad9106_dds")
        by_key = {s.key: s.default_value for s in specs}
        self.assertEqual(by_key["ch2_gain"], 1650)
        self.assertEqual(by_key["ch2_phase"], 32768)
        # Channel 1 and frequency must be untouched.
        self.assertEqual(by_key["ch1_gain"], 0.0)
        self.assertEqual(by_key["ch1_phase"], 0.0)
        self.assertEqual(by_key["frequency_hz"], 1000.0)

    def test_dds_channel_change_ignored_when_no_hardware_selected(self):
        self.event_bus.publish(
            DDS_CHANNEL_CONFIG_CHANGED_TOPIC, DdsChannelConfigChanged(channel=1, gain=100, phase=0)
        )
        self.assertEqual(self.received, [])


if __name__ == "__main__":
    unittest.main()
