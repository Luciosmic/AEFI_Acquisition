import unittest
from unittest.mock import MagicMock
from application.services.excitation_configuration_service.excitation_configuration_service import ExcitationConfigurationService
from application.services.excitation_configuration_service.ports.i_excitation_port import IExcitationPort
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus
from domain.shared_kernel.excitation.events.excitation_frequency_changed.excitation_frequency_changed import (
    ExcitationFrequencyChanged,
)
from domain.shared_kernel.excitation.events.excitation_levels_changed.excitation_levels_changed import (
    ExcitationLevelsChanged,
)
from domain.shared_kernel.excitation.events.dds_channel_config_changed.dds_channel_config_changed import (
    DdsChannelConfigChanged,
)
from domain.shared_kernel.excitation.value_objects.excitation_mode import ExcitationMode
from domain.shared_kernel.excitation.value_objects.excitation_parameters import ExcitationParameters
from tool.diagram_friendly_test import DiagramFriendlyTest


class TestExcitationConfigurationService(DiagramFriendlyTest):

    def setUp(self):
        super().setUp()
        self.port = MagicMock(spec=IExcitationPort)
        self.event_bus = MagicMock(spec=IDomainEventBus)
        self.service = ExcitationConfigurationService(
            excitation_port=self.port, event_bus=self.event_bus
        )

    def test_initial_state_is_off(self):
        params = self.service.get_current_parameters()
        self.assertEqual(params, ExcitationParameters.off())

    def test_set_excitation_calls_port(self):
        self.service.set_excitation(ExcitationMode.X_DIR, 50.0, 50.0, 1000.0)
        self.port.apply_excitation.assert_called_once()

    def test_current_parameters_updated_after_set(self):
        self.service.set_excitation(ExcitationMode.X_DIR, 30.0, 70.0, 1000.0)
        params = self.service.get_current_parameters()
        self.assertAlmostEqual(params.frequency, 1000.0)
        self.assertAlmostEqual(params.level_s1_s2.value, 30.0)
        self.assertAlmostEqual(params.level_s3_s4.value, 70.0)

    def test_set_excitation_publishes_event_when_frequency_changes(self):
        self.service.set_excitation(ExcitationMode.X_DIR, 50.0, 50.0, 1000.0)

        topics = [call.args[0] for call in self.event_bus.publish.call_args_list]
        self.assertIn("excitationfrequencychanged", topics)

    def test_set_excitation_does_not_publish_frequency_when_only_mode_changes(self):
        self.service.set_excitation(ExcitationMode.X_DIR, 50.0, 50.0, 1000.0)
        self.event_bus.reset_mock()

        self.service.set_excitation(ExcitationMode.Y_DIR, 50.0, 50.0, 1000.0)

        self.event_bus.publish.assert_not_called()

    def test_set_excitation_publishes_levels_event_when_levels_change(self):
        self.service.set_excitation(ExcitationMode.X_DIR, 50.0, 50.0, 1000.0)
        self.event_bus.reset_mock()

        self.service.set_excitation(ExcitationMode.X_DIR, 30.0, 70.0, 1000.0)

        self.event_bus.publish.assert_called_once()
        topic, event = self.event_bus.publish.call_args[0]
        self.assertEqual(topic, "excitationlevelschanged")
        self.assertIsInstance(event, ExcitationLevelsChanged)
        self.assertAlmostEqual(event.level_s1_s2_percent, 30.0)
        self.assertAlmostEqual(event.level_s3_s4_percent, 70.0)

    def test_mute_sets_levels_to_zero_keeping_mode_and_frequency(self):
        self.service.set_excitation(ExcitationMode.Y_DIR, 40.0, 60.0, 2000.0)
        self.port.reset_mock()

        self.service.mute()

        self.port.apply_excitation.assert_called_once()
        applied = self.port.apply_excitation.call_args[0][0]
        self.assertEqual(applied.mode, ExcitationMode.Y_DIR)
        self.assertAlmostEqual(applied.frequency, 2000.0)
        self.assertAlmostEqual(applied.level_s1_s2.value, 0.0)
        self.assertAlmostEqual(applied.level_s3_s4.value, 0.0)

    def test_mute_does_not_change_current_parameters(self):
        # Baseline for downstream callers (e.g. ScanExportService metadata) —
        # mute() is a transient hardware toggle, not a config change.
        self.service.set_excitation(ExcitationMode.Y_DIR, 40.0, 60.0, 2000.0)

        self.service.mute()

        params = self.service.get_current_parameters()
        self.assertAlmostEqual(params.level_s1_s2.value, 40.0)
        self.assertAlmostEqual(params.level_s3_s4.value, 60.0)

    def test_mute_does_not_publish_events(self):
        self.service.set_excitation(ExcitationMode.Y_DIR, 40.0, 60.0, 2000.0)
        self.event_bus.reset_mock()

        self.service.mute()

        self.event_bus.publish.assert_not_called()

    def test_unmute_restores_levels_active_before_mute(self):
        self.service.set_excitation(ExcitationMode.Y_DIR, 40.0, 60.0, 2000.0)
        self.service.mute()
        self.port.reset_mock()

        self.service.unmute()

        self.port.apply_excitation.assert_called_once()
        applied = self.port.apply_excitation.call_args[0][0]
        self.assertEqual(applied.mode, ExcitationMode.Y_DIR)
        self.assertAlmostEqual(applied.frequency, 2000.0)
        self.assertAlmostEqual(applied.level_s1_s2.value, 40.0)
        self.assertAlmostEqual(applied.level_s3_s4.value, 60.0)

    def test_unmute_without_prior_mute_is_a_noop(self):
        self.service.set_excitation(ExcitationMode.Y_DIR, 40.0, 60.0, 2000.0)
        self.port.reset_mock()

        self.service.unmute()

        self.port.apply_excitation.assert_not_called()

    def test_unmute_does_not_publish_events(self):
        self.service.set_excitation(ExcitationMode.Y_DIR, 40.0, 60.0, 2000.0)
        self.service.mute()
        self.event_bus.reset_mock()

        self.service.unmute()

        self.event_bus.publish.assert_not_called()

    def test_external_frequency_change_updates_cache_without_republishing(self):
        # Hardware Config tab changes frequency directly on the shared DDS — the
        # service must pick that up via its own subscription, not re-publish it.
        subscribe_call = next(
            call for call in self.event_bus.subscribe.call_args_list
            if call.args[0] == "excitationfrequencychanged"
        )
        handler = subscribe_call.args[1]
        self.event_bus.reset_mock()

        handler(ExcitationFrequencyChanged(frequency_hz=5000.0))

        self.assertAlmostEqual(self.service.get_current_parameters().frequency, 5000.0)
        self.event_bus.publish.assert_not_called()

    def _dds_channel_handler(self):
        subscribe_call = next(
            call for call in self.event_bus.subscribe.call_args_list
            if call.args[0] == "ddschannelconfigchanged"
        )
        return subscribe_call.args[1]

    def test_external_dds_channel_change_updates_level_for_that_channel(self):
        # channel 2 -> DDS2 -> feeds S1/S2 -> level_s1_s2
        handler = self._dds_channel_handler()
        self.event_bus.reset_mock()

        handler(DdsChannelConfigChanged(channel=2, gain=1650, phase=32768))  # 1650/5500 = 30%

        params = self.service.get_current_parameters()
        self.assertAlmostEqual(params.level_s1_s2.value, 30.0)
        self.assertAlmostEqual(params.level_s3_s4.value, 0.0)  # untouched
        self.event_bus.publish.assert_not_called()

    def test_external_dds_channel_change_with_known_phase_pair_sets_matching_mode(self):
        handler = self._dds_channel_handler()

        # X_DIR is (DDS1=0, DDS2=32768) — channel 1 defaults to 0 already.
        handler(DdsChannelConfigChanged(channel=2, gain=5500, phase=32768))

        self.assertEqual(self.service.get_current_parameters().mode, ExcitationMode.X_DIR)

    def test_external_dds_channel_change_with_unknown_phase_falls_back_to_custom(self):
        handler = self._dds_channel_handler()

        handler(DdsChannelConfigChanged(channel=2, gain=5500, phase=16000))

        self.assertEqual(self.service.get_current_parameters().mode, ExcitationMode.CUSTOM)

    def test_external_dds_channel_change_reverts_to_known_mode_when_phase_matches_again(self):
        handler = self._dds_channel_handler()
        handler(DdsChannelConfigChanged(channel=2, gain=5500, phase=16000))  # -> CUSTOM
        self.assertEqual(self.service.get_current_parameters().mode, ExcitationMode.CUSTOM)

        handler(DdsChannelConfigChanged(channel=2, gain=5500, phase=0))  # (0,0) -> Y_DIR

        self.assertEqual(self.service.get_current_parameters().mode, ExcitationMode.Y_DIR)


if __name__ == "__main__":
    unittest.main()
