from domain.calibration.entities.hardware_component_characterization_entry.hardware_component_characterization_entry import (
    HardwareComponentCharacterizationEntry,
)
from domain.calibration.entities.hardware_component_selection.hardware_component_selection import (
    HardwareComponentSelection,
)
from domain.calibration.value_objects.component_characterization.component_characterization import (
    ComponentCharacterization,
)
from domain.calibration.value_objects.hardware_component_kind.hardware_component_kind import (
    HardwareComponentKind,
)
from infrastructure.persistence.calibration.fake.fake_hardware_component_repository import (
    FakeHardwareComponentRepository,
)

ADC = HardwareComponentKind.ADC
MOTORS = HardwareComponentKind.MOTORS


def test_catalog_and_mounting_log_are_append_only_and_split_by_kind():
    repository = FakeHardwareComponentRepository()
    adc = HardwareComponentCharacterizationEntry.single("ADS131A04", ComponentCharacterization.of(ADC, {}))
    motors = HardwareComponentCharacterizationEntry.single("Arcus", ComponentCharacterization.of(MOTORS, {}))
    selection = HardwareComponentSelection.now(ADC, "ADS131A04")

    repository.add(adc)
    repository.add(motors)
    repository.add_selection(selection)

    assert repository.find_all(ADC) == [adc]
    assert repository.find_selections(ADC) == [selection]
    assert repository.find_selections(MOTORS) == []
