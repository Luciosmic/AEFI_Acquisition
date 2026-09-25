import json

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
from infrastructure.persistence.calibration.real_hardware_component_repository import (
    RealHardwareComponentRepository,
)

CONDITIONING = HardwareComponentKind.CONDITIONING_ELECTRONICS_BOARD
EXCITATION = HardwareComponentKind.EXCITATION_ELECTRONICS_BOARD
MCU = HardwareComponentKind.MICROCONTROLLER


def _entry(kind, name, values):
    return HardwareComponentCharacterizationEntry.single(name, ComponentCharacterization.of(kind, values))


def test_empty_registry(tmp_path):
    repository = RealHardwareComponentRepository(tmp_path)

    assert repository.find_all(MCU) == []
    assert repository.find_selections(MCU) == []


def test_entries_and_selections_round_trip_per_kind_file(tmp_path):
    repository = RealHardwareComponentRepository(tmp_path / "nested")
    mcu = _entry(MCU, "STM32", {"optimal_acquisition_rate_per_s": [(1, 1000.0), (10, 800.0)]})
    board = _entry(EXCITATION, "AmpliHT", {})
    selection = HardwareComponentSelection.now(MCU, "STM32")

    repository.add(mcu)
    repository.add(board)
    repository.add_selection(selection)

    assert repository.find_all(MCU) == [mcu]
    assert repository.find_all(EXCITATION) == [board]
    assert repository.find_selections(MCU) == [selection]
    stored = json.loads((tmp_path / "nested" / "hardware_components" / "microcontroller.json").read_text(encoding="utf-8"))
    assert stored["entries"][0]["characterization"] == {
        "max_acquisition_rate_per_s": None,
        "optimal_acquisition_rate_per_s": [[1.0, 1000.0], [10.0, 800.0]],
    }


def test_reads_legacy_signature_tagged_conditioning_entry(tmp_path):
    (tmp_path / "conditioning_electronics_board_calibration.json").write_text(json.dumps({"entries": [{
        "entry_id": "dfa5effc-3fc1-4804-b28a-2ea2bbc9878f",
        "hardware_signature": {
            "excitation_board_version": "AmpliHT_opa462_v2_ASSOCE",
            "conditioning_board_version": "Final_v4_ASSOCE",
            "sensor_version": "v2b",
            "sensor_serial_number": None,
        },
        "response": {"gain": 9.821, "bandwidth_hz": 800000.0},
        "recorded_at": "2026-09-25T13:26:59.336217+00:00",
    }], "selections": [{"board_name": "Final_v4_ASSOCE", "selected_at": "2026-09-25T17:09:14+00:00"}]}),
        encoding="utf-8")
    repository = RealHardwareComponentRepository(tmp_path)

    (entry,) = repository.find_all(CONDITIONING)

    assert entry.component_name == "Final_v4_ASSOCE"
    assert entry.characterization.values == {
        "gain": 9.821, "bandwidth_hz": 800000.0, "noise_density_v_per_sqrt_hz": None,
    }
    assert repository.find_selections(CONDITIONING)[0].component_name == "Final_v4_ASSOCE"


def test_legacy_excitation_file_is_read_then_migrated_on_first_write(tmp_path):
    (tmp_path / "excitation_electronic_board_calibration.json").write_text(json.dumps({
        "entries": [{"entry_id": "8aa60bfd-1c05-45ab-9480-e2be0477d858", "board_name": "AmpliHT",
                     "response": {"gain": 1.0, "bandwidth_hz": None},
                     "recorded_at": "2026-09-25T17:17:29+00:00"}],
        "selections": [],
    }), encoding="utf-8")
    repository = RealHardwareComponentRepository(tmp_path)
    assert [e.component_name for e in repository.find_all(EXCITATION)] == ["AmpliHT"]

    repository.add(_entry(EXCITATION, "AmpliHT", {"bandwidth_hz": 1e6}))

    assert (tmp_path / "hardware_components" / "excitation_electronics_board.json").exists()
    assert len(repository.find_all(EXCITATION)) == 2


def test_find_recovers_from_corrupt_file(tmp_path):
    (tmp_path / "adc_calibration.json").write_text("not valid json", encoding="utf-8")

    assert RealHardwareComponentRepository(tmp_path).find_all(HardwareComponentKind.ADC) == []


def test_mounting_identity_is_persisted(tmp_path):
    repository = RealHardwareComponentRepository(tmp_path)
    selection = HardwareComponentSelection.now(HardwareComponentKind.SENSOR, "v2b_SN-3")

    repository.add_selection(selection)

    assert repository.find_selections(HardwareComponentKind.SENSOR) == [selection]
    assert not (tmp_path / "sensor_calibration.json").exists()  # that file is the angle registry


def test_legacy_mounting_without_identity_gets_a_stable_one(tmp_path):
    (tmp_path / "adc_calibration.json").write_text(json.dumps({
        "entries": [],
        "selections": [{"component_name": "ADS131A04", "selected_at": "2026-09-25T18:18:32+00:00"}],
    }), encoding="utf-8")
    repository = RealHardwareComponentRepository(tmp_path)

    first_read = repository.find_selections(HardwareComponentKind.ADC)[0].mounting_id
    second_read = repository.find_selections(HardwareComponentKind.ADC)[0].mounting_id

    assert first_read == second_read
