import unittest

from application.services.hardware_component_service.hardware_component_service import (
    HARDWARE_COMPONENT_CHARACTERIZED_TOPIC,
    HARDWARE_COMPONENT_MOUNTED_TOPIC,
    HardwareComponentService,
)
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.persistence.calibration.fake.fake_hardware_component_repository import (
    FakeHardwareComponentRepository,
)

SERVICE_LOGGER = "application.services.hardware_component_service.hardware_component_service"
EXCITATION = "excitation_electronics_board"
MCU = "microcontroller"


class TestHardwareComponentService(unittest.TestCase):
    def setUp(self):
        self.repository = FakeHardwareComponentRepository()
        self.event_bus = InMemoryEventBus()
        self.service = HardwareComponentService(repository=self.repository, event_bus=self.event_bus)

    def test_list_kinds_describes_quantities_for_the_ui(self):
        kinds = {k.key: k for k in self.service.list_kinds()}

        self.assertIn("signal_generation_chip", kinds)
        curve = {q.key: q for q in kinds[MCU].quantities}["optimal_acquisition_rate_per_s"]
        self.assertEqual(curve.curve_x_label, "n_avg")

    def test_every_quantity_may_be_left_uncharacterized(self):
        received = []
        self.event_bus.subscribe(HARDWARE_COMPONENT_CHARACTERIZED_TOPIC, received.append)

        with self.assertLogs(SERVICE_LOGGER, level="WARNING") as logs:
            self.service.record_characterization(EXCITATION, "AmpliHT", {"gain": None, "bandwidth_hz": None})

        (component,) = self.service.list_components(EXCITATION)
        self.assertEqual(component.uncharacterized, ("gain", "bandwidth_hz"))
        self.assertIn("gain, bandwidth_hz NOT CHARACTERIZED", logs.output[0])
        self.assertEqual(len(received), 1)

    def test_completing_keeps_history_and_updates_current(self):
        self.service.record_characterization(EXCITATION, "AmpliHT", {})
        self.service.record_characterization(EXCITATION, "AmpliHT", {"gain": 20.0})

        self.assertEqual(len(self.repository.find_all(self.repository_kind(EXCITATION))), 2)
        self.assertEqual(self.service.list_components(EXCITATION)[0].values["gain"], 20.0)

    def test_curve_values_round_trip(self):
        self.service.record_characterization(MCU, "STM32", {"optimal_acquisition_rate_per_s": [(1, 1000), (8, 700)]})

        values = self.service.list_components(MCU)[0].values
        self.assertEqual(values["optimal_acquisition_rate_per_s"], ((1.0, 1000.0), (8.0, 700.0)))

    def test_rejects_non_physical_value_and_blank_name(self):
        with self.assertRaises(ValueError):
            self.service.record_characterization(EXCITATION, "AmpliHT", {"gain": -1.0})
        with self.assertRaises(ValueError):
            self.service.record_characterization(EXCITATION, " ", {})

    def test_mount_component_and_incomplete_configuration(self):
        received = []
        self.event_bus.subscribe(HARDWARE_COMPONENT_MOUNTED_TOPIC, received.append)
        self.service.record_characterization(MCU, "STM32", {})

        with self.assertLogs(SERVICE_LOGGER, level="WARNING") as logs:
            self.assertIsNone(self.service.get_mounted_component(MCU))
        self.assertIn("configuration incomplete", logs.output[0])

        self.service.mount_component(MCU, "STM32")
        self.service.mount_component(MCU, "STM32")  # already mounted: no-op

        self.assertEqual(self.service.get_mounted_component(MCU).component_name, "STM32")
        self.assertEqual(len(received), 1)

    def test_mount_unknown_component_is_refused(self):
        with self.assertRaises(ValueError):
            self.service.mount_component(MCU, "Never_characterized")

    @staticmethod
    def repository_kind(key):
        from domain.calibration.value_objects.hardware_component_kind.hardware_component_kind import (
            HardwareComponentKind,
        )
        return HardwareComponentKind(key)


if __name__ == "__main__":
    unittest.main()
