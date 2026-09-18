"""Tests for AD9106AdvancedConfigurator's ExcitationFrequencyChanged publication."""

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

root_dir = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(root_dir / "src"))

from infrastructure.hardware.micro_controller.MCU_serial_communicator import MCU_SerialCommunicator
from infrastructure.hardware.micro_controller.ad9106.ad9106_controller import AD9106Controller
from infrastructure.hardware.micro_controller.ad9106.ad9106_advanced_configurator import (
    AD9106AdvancedConfigurator,
    DDS_SYNCHRONOUS_DETECTION_CHANNEL_CHANGED_TOPIC,
)
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from domain.shared_kernel.excitation.value_objects.phase_angle import PhaseAngle
from domain.shared_kernel.excitation.events.excitation_frequency_changed.excitation_frequency_changed import (
    ExcitationFrequencyChanged,
)
from domain.shared_kernel.excitation.events.dds_channel_config_changed.dds_channel_config_changed import (
    DdsChannelConfigChanged,
)

_AD9106_LAST_CONFIG_PATH = os.path.join(".aefi_acquisition", "configs", "ad9106_last_config.json")


def _backup_ad9106_last_config() -> "str | None":
    """apply_config() writes to the real relative config path — back it up so
    tests can restore it in tearDown instead of permanently corrupting the
    user's actual last-applied hardware config (this is what happened before:
    a test's partial apply_config() call zeroed out untouched channels on
    disk, and that corruption then got trusted by the real app on next boot)."""
    if os.path.exists(_AD9106_LAST_CONFIG_PATH):
        with open(_AD9106_LAST_CONFIG_PATH, "r") as f:
            return f.read()
    return None


def _restore_ad9106_last_config(backup: "str | None") -> None:
    if backup is not None:
        with open(_AD9106_LAST_CONFIG_PATH, "w") as f:
            f.write(backup)
    elif os.path.exists(_AD9106_LAST_CONFIG_PATH):
        os.remove(_AD9106_LAST_CONFIG_PATH)


class TestAD9106AdvancedConfiguratorFrequencyEvent(unittest.TestCase):
    def setUp(self):
        self._last_config_backup = _backup_ad9106_last_config()
        self._send_patcher = patch.object(MCU_SerialCommunicator, 'send_command', return_value=(True, "OK"))
        self._send_patcher.start()
        self.controller = AD9106Controller(MCU_SerialCommunicator())
        self.event_bus = InMemoryEventBus()
        self.events = []
        self.event_bus.subscribe("excitationfrequencychanged", self.events.append)
        self.configurator = AD9106AdvancedConfigurator(self.controller, self.event_bus)

    def tearDown(self):
        self._send_patcher.stop()
        _restore_ad9106_last_config(self._last_config_backup)

    def test_apply_config_publishes_event_when_frequency_changes(self):
        self.configurator.apply_config({"frequency_hz": 2000.0})

        self.assertEqual(len(self.events), 1)
        self.assertIsInstance(self.events[0], ExcitationFrequencyChanged)
        self.assertEqual(self.events[0].frequency_hz, 2000.0)

    def test_apply_config_does_not_republish_when_frequency_unchanged(self):
        self.configurator.apply_config({"frequency_hz": 2000.0})
        self.configurator.apply_config({"frequency_hz": 2000.0, "ch1_gain": 100.0})

        self.assertEqual(len(self.events), 1)

    def test_apply_config_without_frequency_key_does_not_publish(self):
        self.configurator.apply_config({"ch1_gain": 100.0})

        self.assertEqual(len(self.events), 0)


class TestAD9106AdvancedConfiguratorChannelEvent(unittest.TestCase):
    """ExcitationConfigurationService listens for this to recompute level and
    detect a non-standard phase pair (-> CUSTOM mode) when the Hardware
    Config tab edits channel 1/2 gain/phase directly."""

    def setUp(self):
        self._last_config_backup = _backup_ad9106_last_config()
        self._send_patcher = patch.object(MCU_SerialCommunicator, 'send_command', return_value=(True, "OK"))
        self._send_patcher.start()
        self.controller = AD9106Controller(MCU_SerialCommunicator())
        self.event_bus = InMemoryEventBus()
        self.events = []
        self.event_bus.subscribe("ddschannelconfigchanged", self.events.append)
        self.configurator = AD9106AdvancedConfigurator(self.controller, self.event_bus)

    def tearDown(self):
        self._send_patcher.stop()
        _restore_ad9106_last_config(self._last_config_backup)

    def test_apply_config_publishes_event_for_changed_channel_1_and_2(self):
        # link_dds1_dds2 defaults to True, which would otherwise force ch1/ch2
        # gain equal — disable it here since this test is about independent
        # per-channel writes (see TestAD9106AdvancedConfiguratorLink for the
        # link behavior itself).
        self.configurator.apply_config({
            "link_dds1_dds2": False,
            "ch1_gain": 1000, "ch1_phase": 0, "ch2_gain": 2000, "ch2_phase": 16000,
        })

        self.assertEqual({e.channel for e in self.events}, {1, 2})
        by_channel = {e.channel: e for e in self.events}
        self.assertEqual(by_channel[1].gain, 1000)
        self.assertEqual(by_channel[1].phase, 0)
        self.assertEqual(by_channel[2].gain, 2000)
        self.assertEqual(by_channel[2].phase, 16000)

    def test_apply_config_does_not_publish_for_channels_3_and_4(self):
        self.configurator.apply_config({"ch3_gain": 5000, "ch4_phase": 100})

        self.assertEqual(self.events, [])

    def test_apply_config_does_not_republish_unchanged_channel(self):
        self.configurator.apply_config({"link_dds1_dds2": False, "ch1_gain": 1000, "ch1_phase": 0})
        self.configurator.apply_config({"link_dds1_dds2": False, "ch1_gain": 1000, "ch1_phase": 0})

        self.assertEqual(len(self.events), 1)

    def test_apply_config_republishes_when_only_phase_changes(self):
        self.configurator.apply_config({"link_dds1_dds2": False, "ch1_gain": 1000, "ch1_phase": 0})
        self.configurator.apply_config({"link_dds1_dds2": False, "ch1_gain": 1000, "ch1_phase": 16000})

        self.assertEqual(len(self.events), 2)
        self.assertEqual(self.events[-1].phase, 16000)


class TestAD9106AdvancedConfiguratorLink(unittest.TestCase):
    """DDS1/DDS2 gain link: prevents the desync bug where changing a single
    channel's gain from the Hardware Advanced tab silently broke the pair
    while the Excitation panel's "Link" checkbox still showed checked."""

    def setUp(self):
        self._last_config_backup = _backup_ad9106_last_config()
        self._send_patcher = patch.object(MCU_SerialCommunicator, 'send_command', return_value=(True, "OK"))
        self._send_patcher.start()
        self.controller = AD9106Controller(MCU_SerialCommunicator())
        self.event_bus = InMemoryEventBus()
        self.channel_events = []
        self.link_events = []
        self.event_bus.subscribe("ddschannelconfigchanged", self.channel_events.append)
        self.event_bus.subscribe("excitationddslinkchanged", self.link_events.append)
        self.configurator = AD9106AdvancedConfigurator(self.controller, self.event_bus)

    def tearDown(self):
        self._send_patcher.stop()
        _restore_ad9106_last_config(self._last_config_backup)

    def test_link_defaults_to_true_and_mirrors_single_channel_edit(self):
        """Only ch1_gain is sent (as if the panel only exposed one field) —
        with the link on by default, ch2 must still end up at the same gain."""
        self.configurator.apply_config({"ch1_gain": 3000})

        gains = self.controller.get_memory_state()["DDS"]["Gain"]
        self.assertEqual(gains[1], 3000)
        self.assertEqual(gains[2], 3000)

    def test_linked_apply_with_disagreeing_gains_mirrors_the_changed_one(self):
        self.configurator.apply_config({"link_dds1_dds2": False, "ch1_gain": 1000, "ch2_gain": 1000})
        self.channel_events.clear()

        # ch1 moves to 4000 while ch2 stays at its old value in the same dict
        # (exactly what a full-panel-snapshot Apply looks like when only one
        # spinbox was actually edited) — with the link re-enabled, ch2 must
        # follow ch1, not the other way around.
        self.configurator.apply_config({"link_dds1_dds2": True, "ch1_gain": 4000, "ch2_gain": 1000})

        gains = self.controller.get_memory_state()["DDS"]["Gain"]
        self.assertEqual(gains[1], 4000)
        self.assertEqual(gains[2], 4000)

    def test_disabling_link_allows_independent_gains_again(self):
        self.configurator.apply_config({"ch1_gain": 2000})  # linked by default -> ch2 mirrors
        self.configurator.apply_config({"link_dds1_dds2": False, "ch1_gain": 2000, "ch2_gain": 9000})

        gains = self.controller.get_memory_state()["DDS"]["Gain"]
        self.assertEqual(gains[1], 2000)
        self.assertEqual(gains[2], 9000)

    def test_link_toggle_publishes_excitation_dds_link_changed(self):
        self.configurator.apply_config({"link_dds1_dds2": False})

        self.assertEqual(len(self.link_events), 1)
        self.assertFalse(self.link_events[0].linked)

    def test_link_toggle_does_not_republish_unchanged_value(self):
        self.configurator.apply_config({"link_dds1_dds2": True})
        self.configurator.apply_config({"link_dds1_dds2": True})

        self.assertEqual(len(self.link_events), 1)

    def test_link_persisted_to_last_config(self):
        self.configurator.apply_config({"link_dds1_dds2": False})

        with open(_AD9106_LAST_CONFIG_PATH, "r") as f:
            saved = json.load(f)
        self.assertFalse(saved["link_dds1_dds2"])


class TestAD9106AdvancedConfiguratorDds3Dds4GainLink(unittest.TestCase):
    """DDS3/DDS4 gain link: the two synchronous-detection (I/Q) channels
    must share the same gain, or lock-in amplitude scaling breaks — mirror
    of TestAD9106AdvancedConfiguratorLink but config-only (no UI toggle),
    same pattern as _enforce_dds3_dds4_quadrature."""

    def setUp(self):
        self._last_config_backup = _backup_ad9106_last_config()
        self._send_patcher = patch.object(MCU_SerialCommunicator, 'send_command', return_value=(True, "OK"))
        self._send_patcher.start()
        self.controller = AD9106Controller(MCU_SerialCommunicator())
        self.event_bus = InMemoryEventBus()
        self.configurator = AD9106AdvancedConfigurator(self.controller, self.event_bus)

    def tearDown(self):
        self._send_patcher.stop()
        _restore_ad9106_last_config(self._last_config_backup)

    def test_link_defaults_to_true_and_mirrors_single_channel_edit(self):
        self.configurator.apply_config({"ch3_gain": 3000})

        gains = self.controller.get_memory_state()["DDS"]["Gain"]
        self.assertEqual(gains[3], 3000)
        self.assertEqual(gains[4], 3000)

    def test_linked_apply_with_disagreeing_gains_mirrors_the_changed_one(self):
        self.configurator.apply_config({"link_dds3_dds4_gain": False, "ch3_gain": 1000, "ch4_gain": 1000})

        # ch3 moves to 4000 while ch4 stays at its old value in the same dict
        # (a full-panel-snapshot Apply where only ch3's spinbox was edited).
        self.configurator.apply_config({"link_dds3_dds4_gain": True, "ch3_gain": 4000, "ch4_gain": 1000})

        gains = self.controller.get_memory_state()["DDS"]["Gain"]
        self.assertEqual(gains[3], 4000)
        self.assertEqual(gains[4], 4000)

    def test_disabling_link_allows_independent_gains_again(self):
        self.configurator.apply_config({"ch3_gain": 2000})  # linked by default -> ch4 mirrors
        self.configurator.apply_config({"link_dds3_dds4_gain": False, "ch3_gain": 2000, "ch4_gain": 9000})

        gains = self.controller.get_memory_state()["DDS"]["Gain"]
        self.assertEqual(gains[3], 2000)
        self.assertEqual(gains[4], 9000)

    def test_link_persisted_to_last_config(self):
        self.configurator.apply_config({"link_dds3_dds4_gain": False})

        with open(_AD9106_LAST_CONFIG_PATH, "r") as f:
            saved = json.load(f)
        self.assertFalse(saved["link_dds3_dds4_gain"])

    def test_link_defaults_to_true_when_never_set(self):
        self.configurator.apply_config({"ch1_gain": 100})

        with open(_AD9106_LAST_CONFIG_PATH, "r") as f:
            saved = json.load(f)
        self.assertTrue(saved["link_dds3_dds4_gain"])


class TestAD9106AdvancedConfiguratorSynchronousDetectionChannelEvent(unittest.TestCase):
    """ch3/ch4 changes must publish on their own separate topic — NEVER on
    DDS_CHANNEL_CONFIG_CHANGED_TOPIC, which ExcitationConfigurationService
    treats as exclusively channel 1/2 (any channel != 1 is read as channel 2,
    so a ch3/ch4 event there would corrupt its excitation mode/level)."""

    def setUp(self):
        self._last_config_backup = _backup_ad9106_last_config()
        self._send_patcher = patch.object(MCU_SerialCommunicator, 'send_command', return_value=(True, "OK"))
        self._send_patcher.start()
        self.controller = AD9106Controller(MCU_SerialCommunicator())
        self.event_bus = InMemoryEventBus()
        self.configurator = AD9106AdvancedConfigurator(self.controller, self.event_bus)

    def tearDown(self):
        self._send_patcher.stop()
        _restore_ad9106_last_config(self._last_config_backup)

    def test_ch3_edit_publishes_on_synchronous_detection_topic_not_excitation_topic(self):
        from infrastructure.hardware.micro_controller.ad9106.ad9106_advanced_configurator import (
            DDS_SYNCHRONOUS_DETECTION_CHANNEL_CHANGED_TOPIC,
            DDS_CHANNEL_CONFIG_CHANGED_TOPIC,
        )

        excitation_events = []
        sync_events = []
        self.event_bus.subscribe(DDS_CHANNEL_CONFIG_CHANGED_TOPIC, lambda e: excitation_events.append(e))
        self.event_bus.subscribe(DDS_SYNCHRONOUS_DETECTION_CHANNEL_CHANGED_TOPIC, lambda e: sync_events.append(e))

        self.configurator.apply_config({"ch3_phase": 16384, "ch3_gain": 10000})

        self.assertEqual(excitation_events, [])
        # ch3's own change AND the quadrature-derived ch4 change both fire
        # (see the dedicated ch4-derivation test below) — assert ch3's event
        # specifically rather than the total count.
        ch3_event = next(e for e in sync_events if e.channel == 3)
        self.assertEqual(ch3_event.phase, 16384)

    def test_ch4_quadrature_derived_value_also_publishes_on_synchronous_detection_topic(self):
        from infrastructure.hardware.micro_controller.ad9106.ad9106_advanced_configurator import (
            DDS_SYNCHRONOUS_DETECTION_CHANNEL_CHANGED_TOPIC,
        )

        # Establish a DIFFERENT ch3 baseline first — otherwise this test can
        # coincidentally pass/fail depending on whatever ch3 value a PRIOR
        # test run already persisted to ad9106_last_config.json (the "ch3
        # unchanged -> skip re-deriving ch4" guard would then wrongly treat
        # this call as a no-op).
        self.configurator.apply_config({"ch3_phase": 0})

        sync_events = []
        self.event_bus.subscribe(DDS_SYNCHRONOUS_DETECTION_CHANNEL_CHANGED_TOPIC, lambda e: sync_events.append(e))

        self.configurator.apply_config({"ch3_phase": 16384})  # ch4 auto-derives to 0

        channels = {e.channel for e in sync_events}
        self.assertEqual(channels, {3, 4})
        ch4_event = next(e for e in sync_events if e.channel == 4)
        self.assertEqual(ch4_event.phase, 0)


class TestAD9106AdvancedConfiguratorQuadratureEnforcement(unittest.TestCase):
    """ch4 must always mirror ch3 at -90° (quadrature I/Q reference for the
    synchronous detection demodulation) — unidirectional, unlike the
    ch1/ch2 gain link: ch3 is the sole source of truth, ch4 never feeds back."""

    def setUp(self):
        self._last_config_backup = _backup_ad9106_last_config()
        self._send_patcher = patch.object(MCU_SerialCommunicator, 'send_command', return_value=(True, "OK"))
        self._send_patcher.start()
        self.controller = AD9106Controller(MCU_SerialCommunicator())
        self.event_bus = InMemoryEventBus()
        self.configurator = AD9106AdvancedConfigurator(self.controller, self.event_bus)

    def tearDown(self):
        self._send_patcher.stop()
        _restore_ad9106_last_config(self._last_config_backup)

    def test_ch4_derived_from_ch3_when_enforced_by_default(self):
        # ch3 at 90 degrees (16384 register) -> ch4 should land at 0 degrees (0 register),
        # matching the default config template convention (ch3=90, ch4=0).
        self.configurator.apply_config({"ch3_phase": 16384})

        phases = self.controller.get_memory_state()["DDS"]["Phase"]
        self.assertEqual(phases[4], 0)

    def test_no_op_when_flag_explicitly_disabled(self):
        self.configurator.apply_config({
            "enforce_dds3_dds4_quadrature": False, "ch3_phase": 16384, "ch4_phase": 5000,
        })

        phases = self.controller.get_memory_state()["DDS"]["Phase"]
        self.assertEqual(phases[4], 5000)

    def test_no_op_when_ch3_phase_absent(self):
        self.configurator.apply_config({"ch4_phase": 12345})

        phases = self.controller.get_memory_state()["DDS"]["Phase"]
        self.assertEqual(phases[4], 12345)

    def test_enforce_dds3_dds4_quadrature_persisted_to_last_config(self):
        self.configurator.apply_config({"enforce_dds3_dds4_quadrature": False})

        with open(_AD9106_LAST_CONFIG_PATH, "r") as f:
            saved = json.load(f)
        self.assertFalse(saved["enforce_dds3_dds4_quadrature"])

    def test_enforce_dds3_dds4_quadrature_defaults_to_true_when_never_set(self):
        self.configurator.apply_config({"ch1_gain": 100})

        with open(_AD9106_LAST_CONFIG_PATH, "r") as f:
            saved = json.load(f)
        self.assertTrue(saved["enforce_dds3_dds4_quadrature"])

    def test_is_dds3_dds4_quadrature_enforced_reflects_persisted_flag(self):
        self.configurator.apply_config({"enforce_dds3_dds4_quadrature": False})

        self.assertFalse(self.configurator.is_dds3_dds4_quadrature_enforced())

    def test_direct_ch4_edit_survives_a_full_config_resubmission_with_unchanged_ch3(self):
        # Regression: HardwareAdvancedConfigPanel is a generic panel that
        # resubmits EVERY widget's current value on every Apply click, not
        # just the one the user touched. Before this fix, ch3_phase being
        # merely PRESENT in that full resubmission (even at its unchanged
        # value) was enough to make _enforce_dds3_dds4_quadrature silently
        # recompute and discard a direct, independent ch4 edit submitted in
        # the same call.
        self.configurator.apply_config({"ch3_phase": 16384})  # establish ch3 = 90deg

        # Full resubmission: ch3 unchanged, ch4 set directly to something
        # that does NOT match the quadrature-derived value (0).
        self.configurator.apply_config({"ch3_phase": 16384, "ch4_phase": 40000})

        phases = self.controller.get_memory_state()["DDS"]["Phase"]
        self.assertEqual(phases[4], 40000)

    def test_ch4_still_re_derives_when_ch3_genuinely_changes_in_a_full_resubmission(self):
        self.configurator.apply_config({"ch3_phase": 16384})  # ch3 = 90deg -> ch4 = 0deg

        # Full resubmission where ch3 is intentionally moved to 0deg; any
        # co-submitted ch4 value must still be overridden by the derivation.
        self.configurator.apply_config({"ch3_phase": 0, "ch4_phase": 40000})

        phases = self.controller.get_memory_state()["DDS"]["Phase"]
        self.assertEqual(phases[3], 0)
        self.assertEqual(phases[4], PhaseAngle(270.0).to_register())  # 0 - 90 mod 360


class TestAD9106AdvancedConfiguratorPersistFlag(unittest.TestCase):
    """apply_config(config, persist=False) writes hardware registers and
    still publishes change events, but must NEVER touch
    ad9106_last_config.json — used by synchronous-detection compensation
    writes, which are transient/programmatic and must not overwrite the
    user's manually-tuned baseline (see AdapterSynchronousDetectionAD9106)."""

    def setUp(self):
        self._last_config_backup = _backup_ad9106_last_config()
        self._send_patcher = patch.object(MCU_SerialCommunicator, 'send_command', return_value=(True, "OK"))
        self._send_patcher.start()
        self.controller = AD9106Controller(MCU_SerialCommunicator())
        self.event_bus = InMemoryEventBus()
        self.configurator = AD9106AdvancedConfigurator(self.controller, self.event_bus)

    def tearDown(self):
        self._send_patcher.stop()
        _restore_ad9106_last_config(self._last_config_backup)

    def test_persist_false_writes_hardware_register(self):
        self.configurator.apply_config({"ch3_phase": 12345}, persist=False)

        self.assertEqual(self.controller.get_memory_state()["DDS"]["Phase"][3], 12345)

    def test_persist_false_does_not_create_or_modify_last_config_file(self):
        # No manual baseline yet — persist=False must not create the file either.
        if os.path.exists(_AD9106_LAST_CONFIG_PATH):
            os.remove(_AD9106_LAST_CONFIG_PATH)

        self.configurator.apply_config({"ch3_phase": 12345}, persist=False)

        self.assertFalse(os.path.exists(_AD9106_LAST_CONFIG_PATH))

    def test_persist_false_does_not_overwrite_an_existing_manual_baseline(self):
        self.configurator.apply_config({"ch3_phase": 5000})  # persist=True (default): manual baseline
        with open(_AD9106_LAST_CONFIG_PATH, "r") as f:
            baseline = json.load(f)

        self.configurator.apply_config({"ch3_phase": 20000}, persist=False)  # compensation write

        with open(_AD9106_LAST_CONFIG_PATH, "r") as f:
            after = json.load(f)
        self.assertEqual(after, baseline)

    def test_persist_false_still_publishes_synchronous_detection_channel_event(self):
        received = []
        self.event_bus.subscribe(
            DDS_SYNCHRONOUS_DETECTION_CHANNEL_CHANGED_TOPIC, lambda e: received.append(e)
        )

        self.configurator.apply_config({"ch3_phase": 12345}, persist=False)

        self.assertTrue(any(e.channel == 3 and e.phase == 12345 for e in received))


class TestNestedChannelsToFlatConfig(unittest.TestCase):
    """Pure conversion helper used by MCULifecycleAdapter to delegate startup
    DDS config application onto apply_config() (the single writer)."""

    def test_converts_frequency_and_all_channel_fields(self):
        nested = {
            "frequency_hz": 10000.0,
            "channels": {
                "1": {"gain": 0, "phase": 0, "offset": 0},
                "3": {"gain": 10000, "phase": 16384, "offset": 0},
            },
        }

        flat = AD9106AdvancedConfigurator.nested_channels_to_flat_config(nested)

        self.assertEqual(flat["frequency_hz"], 10000.0)
        self.assertEqual(flat["ch1_gain"], 0)
        self.assertEqual(flat["ch1_phase"], 0)
        self.assertEqual(flat["ch1_offset"], 0)
        self.assertEqual(flat["ch3_gain"], 10000)
        self.assertEqual(flat["ch3_phase"], 16384)

    def test_omits_keys_not_present_in_nested_config(self):
        flat = AD9106AdvancedConfigurator.nested_channels_to_flat_config({"channels": {"2": {"gain": 500}}})

        self.assertEqual(flat, {"ch2_gain": 500})
        self.assertNotIn("frequency_hz", flat)
        self.assertNotIn("ch2_phase", flat)

    def test_empty_nested_config_yields_empty_flat_config(self):
        self.assertEqual(AD9106AdvancedConfigurator.nested_channels_to_flat_config({}), {})


class TestAD9106AdvancedConfiguratorDefaultCh3Gain(unittest.TestCase):
    """get_default_ch3_gain() reads the pure default template — used by the
    Excitation panel's "Enable Lock-In Detection" warning/reset feature."""

    def setUp(self):
        self._last_config_backup = _backup_ad9106_last_config()
        self._send_patcher = patch.object(MCU_SerialCommunicator, 'send_command', return_value=(True, "OK"))
        self._send_patcher.start()
        self.controller = AD9106Controller(MCU_SerialCommunicator())
        self.event_bus = InMemoryEventBus()
        self.configurator = AD9106AdvancedConfigurator(self.controller, self.event_bus)

    def tearDown(self):
        self._send_patcher.stop()
        _restore_ad9106_last_config(self._last_config_backup)

    def test_reads_ch3_gain_from_default_template(self):
        default_path = _AD9106_LAST_CONFIG_PATH.replace("last_config", "default_config")
        with open(default_path, "r") as f:
            default_config = json.load(f)

        self.assertEqual(
            self.configurator.get_default_ch3_gain(), default_config["channels"]["3"]["gain"]
        )


class TestAD9106AdvancedConfiguratorResetToDefault(unittest.TestCase):
    """reset_to_default() is the counterpart to save_config_as_default(): it
    discards whatever is in ad9106_last_config.json and re-applies the
    factory ad9106_default_config.json — to hardware, not just to disk."""

    def setUp(self):
        self._last_config_backup = _backup_ad9106_last_config()
        self._send_patcher = patch.object(MCU_SerialCommunicator, 'send_command', return_value=(True, "OK"))
        self._send_patcher.start()
        self.controller = AD9106Controller(MCU_SerialCommunicator())
        self.event_bus = InMemoryEventBus()
        self.configurator = AD9106AdvancedConfigurator(self.controller, self.event_bus)

        default_path = _AD9106_LAST_CONFIG_PATH.replace("last_config", "default_config")
        with open(default_path, "r") as f:
            self.default_config = json.load(f)

    def tearDown(self):
        self._send_patcher.stop()
        _restore_ad9106_last_config(self._last_config_backup)

    def test_reset_to_default_applies_default_gain_to_hardware(self):
        # Drift away from default first.
        self.configurator.apply_config({"link_dds1_dds2": False, "ch3_gain": 1, "ch4_gain": 1})

        self.configurator.reset_to_default()

        gains = self.controller.get_memory_state()["DDS"]["Gain"]
        default_channels = self.default_config["channels"]
        self.assertEqual(gains[3], default_channels["3"]["gain"])
        self.assertEqual(gains[4], default_channels["4"]["gain"])

    def test_reset_to_default_persists_default_to_last_config(self):
        self.configurator.apply_config({"link_dds1_dds2": False, "ch1_gain": 999})

        self.configurator.reset_to_default()

        with open(_AD9106_LAST_CONFIG_PATH, "r") as f:
            saved = json.load(f)
        self.assertEqual(saved["channels"]["1"]["gain"], self.default_config["channels"]["1"]["gain"])
        self.assertEqual(saved["link_dds1_dds2"], self.default_config["link_dds1_dds2"])

    def test_reset_to_default_publishes_frequency_changed_when_drifted(self):
        events = []
        self.event_bus.subscribe("excitationfrequencychanged", events.append)
        self.configurator.apply_config({"frequency_hz": 999999.0})
        events.clear()

        self.configurator.reset_to_default()

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].frequency_hz, self.default_config["frequency_hz"])


class TestAD9106AdvancedConfiguratorReloadLastConfig(unittest.TestCase):
    """reload_last_config() is the counterpart to reset_to_default(): it
    re-applies whatever is in ad9106_last_config.json (the last MANUAL
    setting) to hardware — used to discard a transient persist=False write
    (synchronous-detection compensation) when compensation is disabled."""

    def setUp(self):
        self._last_config_backup = _backup_ad9106_last_config()
        self._send_patcher = patch.object(MCU_SerialCommunicator, 'send_command', return_value=(True, "OK"))
        self._send_patcher.start()
        self.controller = AD9106Controller(MCU_SerialCommunicator())
        self.event_bus = InMemoryEventBus()
        self.configurator = AD9106AdvancedConfigurator(self.controller, self.event_bus)

    def tearDown(self):
        self._send_patcher.stop()
        _restore_ad9106_last_config(self._last_config_backup)

    def test_reload_last_config_restores_manual_baseline_after_a_transient_write(self):
        self.configurator.apply_config({"ch3_phase": 5000})  # manual baseline, persisted

        self.configurator.apply_config({"ch3_phase": 20000}, persist=False)  # transient (compensation)
        self.assertEqual(self.controller.get_memory_state()["DDS"]["Phase"][3], 20000)

        self.configurator.reload_last_config()

        self.assertEqual(self.controller.get_memory_state()["DDS"]["Phase"][3], 5000)

    def test_reload_last_config_is_a_no_op_when_no_manual_baseline_exists(self):
        if os.path.exists(_AD9106_LAST_CONFIG_PATH):
            os.remove(_AD9106_LAST_CONFIG_PATH)

        # Must not raise even with nothing to reload.
        self.configurator.reload_last_config()


if __name__ == "__main__":
    unittest.main()
