import unittest
from uuid import uuid4

from domain.test_bench_configuration.bench_configuration import BenchConfiguration
from domain.test_bench_configuration.events.hardware_component_events.hardware_component_events import (
    HardwareComponentCharacterized,
    HardwareComponentMounted,
)
from domain.test_bench_configuration.value_objects.hardware_component_kind.hardware_component_kind import (
    HardwareComponentKind,
)
from domain.test_bench_configuration.value_objects.hardware_signature.hardware_signature import HardwareSignature


def make_hardware_signature(**overrides: Any) -> HardwareSignature:
    defaults: dict[str, Any] = dict(
        excitation_electronics_board_name="v1.2",
        conditioning_electronics_board_name="v2.0",
        sensor_name="v3.1_SN-001",
    )
    defaults.update(overrides)
    return HardwareSignature(**defaults)


class TestBenchConfiguration(unittest.TestCase):
    def test_mounting_gets_its_own_identity_carried_by_the_event(self):
        configuration = BenchConfiguration()

        selection = configuration.mount_hardware_component(HardwareComponentKind.SENSOR, "v2b_SN-3", {"v2b_SN-3"}, None)

        (event,) = configuration.domain_events
        self.assertEqual(event.mounting_id, selection.mounting_id)

    def test_record_hardware_component_characterization_emits_event(self):
        configuration = BenchConfiguration()

        entry = configuration.record_hardware_component_characterization(
            HardwareComponentKind.EXCITATION_ELECTRONICS_BOARD, "AmpliHT_v2", {"bandwidth_hz": 1e6}
        )

        self.assertEqual(entry.component_name, "AmpliHT_v2")
        self.assertEqual(entry.characterization.uncharacterized(), ["gain"])
        (event,) = configuration.domain_events
        self.assertIsInstance(event, HardwareComponentCharacterized)

    def test_mount_hardware_component_records_selection_and_emits_event(self):
        configuration = BenchConfiguration()

        selection = configuration.mount_hardware_component(HardwareComponentKind.ADC, "B", {"A", "B"}, "A")

        self.assertEqual(selection.component_name, "B")
        (event,) = configuration.domain_events
        self.assertIsInstance(event, HardwareComponentMounted)

    def test_mount_refuses_uncharacterized_component(self):
        configuration = BenchConfiguration()
        with self.assertRaises(ValueError):
            configuration.mount_hardware_component(HardwareComponentKind.ADC, "Unknown", {"A"}, None)
        self.assertEqual(configuration.domain_events, [])

    def test_mount_already_mounted_component_is_a_logged_no_op(self):
        configuration = BenchConfiguration()
        with self.assertLogs("domain.test_bench_configuration.bench_configuration", level="INFO") as logs:
            self.assertIsNone(configuration.mount_hardware_component(HardwareComponentKind.ADC, "A", {"A"}, "A"))
        self.assertEqual(configuration.domain_events, [])
        self.assertIn("already mounted", logs.output[0])

    def test_mounted_component_is_latest_selection(self):
        from datetime import datetime, timezone
        from domain.test_bench_configuration.entities.hardware_component_selection.hardware_component_selection import (
            HardwareComponentSelection,
        )
        kind = HardwareComponentKind.MOTORS
        selections = [
            HardwareComponentSelection(kind, "B", datetime(2026, 6, 1, tzinfo=timezone.utc), uuid4()),
            HardwareComponentSelection(kind, "A", datetime(2026, 1, 1, tzinfo=timezone.utc), uuid4()),
        ]
        self.assertEqual(BenchConfiguration.mounted_component_name(selections), "B")
        self.assertIsNone(BenchConfiguration.mounted_component_name([]))

    def test_current_characterization_is_latest_entry_of_that_component(self):
        record = BenchConfiguration().record_hardware_component_characterization
        kind = HardwareComponentKind.EXCITATION_ELECTRONICS_BOARD
        first = record(kind, "A", {})
        completed = record(kind, "A", {"gain": 20.0})
        other = record(kind, "B", {})

        self.assertEqual(BenchConfiguration.current_characterization([first, completed, other], "A"), completed)
        self.assertIsNone(BenchConfiguration.current_characterization([first], None))

    def test_is_component_already_recorded_by_name_only(self):
        record = BenchConfiguration().record_hardware_component_characterization
        kind = HardwareComponentKind.EXCITATION_ELECTRONICS_BOARD
        entries = [record(kind, "A", {})]

        self.assertTrue(BenchConfiguration.is_component_already_recorded(entries, "A"))
        self.assertFalse(BenchConfiguration.is_component_already_recorded(entries, "B"))
        self.assertFalse(BenchConfiguration.is_component_already_recorded([], "A"))

    def test_resolve_current_hardware_signature_warns_per_board_kind_not_mounted(self):
        fallback = make_hardware_signature()

        with self.assertLogs("domain.test_bench_configuration.bench_configuration", level="WARNING") as logs:
            resolved = BenchConfiguration.resolve_current_hardware_signature(fallback, None, None, None)

        self.assertEqual(resolved, fallback)
        self.assertEqual(len(logs.records), 3)  # sensor + both boards on the template

    def test_resolve_current_hardware_signature_uses_mounted_board_names(self):
        resolved = BenchConfiguration.resolve_current_hardware_signature(
            make_hardware_signature(), "cond_X", "exc_Y", "sensor_Z"
        )

        self.assertEqual(resolved.conditioning_electronics_board_name, "cond_X")
        self.assertEqual(resolved.excitation_electronics_board_name, "exc_Y")
        self.assertEqual(resolved.sensor_name, "sensor_Z")
