import csv
import json
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from application.services.frequency_sweep_service.dtos.acquisition_parameters_dtos import (
    FrequencySweepAcquisitionParametersDTO,
    FrequencySweepActivityDTO,
    SweptExcitationDTO,
)
from application.services.frequency_sweep_service.dtos.frequency_sweep_dtos import (
    FrequencyPointDTO,
    FrequencySweepResultDTO,
    FrequencySweepSampleDTO,
)
from application.services.frequency_sweep_service.frequency_sweep_service import CONTROLLER
from application.shared.acquisition_parameters.acquisition_conditions_dtos import BenchPositionDTO, ExportedFileDTO
from infrastructure.acquisition_conditions.fake.fake_acquisition_conditions import make_bench_conditions
from infrastructure.persistence.acquisition_parameters.acquisition_parameters_v1 import UCUM_UNITS
from infrastructure.persistence.acquisition_throughput._tests.acquisition_parameters_v1_serializer_test import (
    UCUM_SYNTAX,
    numbers_outside_quantities,
    units,
)
from infrastructure.persistence.frequency_sweep.acquisition_parameters_v1_serializer import (
    COLUMNS,
    serialize_acquisition_parameters_v1,
)
from infrastructure.persistence.frequency_sweep.csv_frequency_sweep_export_port import CsvFrequencySweepExportPort
from infrastructure.provenance.fake.fake_provenance import CLEAN

FREQUENCIES = (100.0, 1000.0, 10000.0)
ACTIVITY = FrequencySweepActivityDTO(
    activity_id="sweep-1",
    started_at=datetime(2026, 11, 12, 12, 0, 0, tzinfo=timezone.utc),
    status="completed",
    role="background",
    frequencies_hz=FREQUENCIES,
    samples_per_frequency=50,
    table_height_mm=42.5,
    settle_delay_s=0.5,
    frequency_timeout_s=60.0,
    controller=CONTROLLER,
    held_controls=("excitation", "acquisition_stream"),
    excitation=SweptExcitationDTO("X_DIR", 40.0, 40.0, 1000.0),
    stream_started_here=True,
    operator_name="Luis",
    operator_id="op-1",
    ended_at=datetime(2026, 11, 12, 12, 5, 0, tzinfo=timezone.utc),
    acquired_frequency_count=3,
    excitation_restored=True,
    bench_position_start=BenchPositionDTO(12.5, -3.0),
    bench_position_end=BenchPositionDTO(12.5, -3.0),
    usb_latency_timer_ms=1.0,
)
PARAMETERS = FrequencySweepAcquisitionParametersDTO(
    activity=ACTIVITY, conditions=make_bench_conditions(), software=CLEAN,
    files=(ExportedFileDTO("frequency_response.csv", "CSV", 100, "a" * 64),),
)
RESULT = FrequencySweepResultDTO(
    sweep_id="sweep-1", role="background", table_height_mm=42.5, status="completed", export_path=None,
    points=tuple(
        FrequencyPointDTO(i, f, 2, (1e-3,) * 6, (1e-6,) * 6, None if i == 0 else 90.0) for i, f in enumerate(FREQUENCIES)
    ),
)
SAMPLES = [
    FrequencySweepSampleDTO(f, i, datetime(2026, 11, 12, 12, 0, i), (0.0,) * 6) for f in FREQUENCIES for i in range(2)
]
CLOCK = datetime(2026, 11, 12, 13, 0, 0)
GENERATED = datetime(2026, 11, 12, 13, 0, 0, tzinfo=timezone.utc)


def serialize(parameters=PARAMETERS):
    return serialize_acquisition_parameters_v1(parameters, GENERATED)


class TestFrequencySweepAcquisitionParameters(unittest.TestCase):
    def test_every_number_is_a_quantity_with_a_known_ucum_unit(self):
        document = json.loads(json.dumps(serialize()))
        self.assertEqual(numbers_outside_quantities(document), [])
        for path, unit in units(document):
            with self.subTest(path=path):
                self.assertIn(unit, UCUM_UNITS)
                self.assertRegex(unit, UCUM_SYNTAX)

    def test_procedure_states_role_grid_and_table_height_given_by_the_operator(self):
        document = serialize()
        self.assertEqual(document["schema"]["version"], "1.4")
        self.assertEqual(document["provenance"]["activity"]["kind"], "frequency_sweep")
        self.assertEqual(document["provenance"]["operator"], {"id": "op-1", "name": "Luis"})
        procedure = document["procedure"]["frequency_sweep"]
        self.assertEqual(procedure["role"], "background")
        self.assertEqual(procedure["frequency_grid"]["value"], list(FREQUENCIES))
        self.assertEqual(procedure["frequency_grid"]["unit"], "Hz")
        self.assertEqual(procedure["table_height"]["value"], 42.5)
        self.assertEqual(procedure["table_height"]["unit"], "mm")
        self.assertEqual(procedure["table_height"]["source"], "operator")
        self.assertFalse(document["feature_of_interest"]["present"])

    def test_the_swept_frequency_refers_to_the_grid_instead_of_the_start_value(self):
        document = serialize()
        chip_frequency = document["components"]["signal_generation_chip"]["settings"]["frequency"]
        self.assertEqual(chip_frequency["derived_from"], "procedure.frequency_sweep.frequency_grid")
        excitation = document["measurement_chain"]["excitation"]["state"]
        self.assertEqual(excitation["operator_frequency"], {"value": 1000.0, "unit": "Hz"})

    def test_an_incomplete_sweep_is_warned_as_unusable(self):
        cancelled = replace(PARAMETERS, activity=replace(ACTIVITY, status="cancelled", acquired_frequency_count=1))
        paths = [w["path"] for w in serialize(cancelled)["warnings"]]
        self.assertIn("procedure.frequency_sweep.acquired_frequency_count", paths)
        self.assertNotIn("procedure.frequency_sweep.acquired_frequency_count", [w["path"] for w in serialize()["warnings"]])


class TestCsvFrequencySweepExportPort(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.port = CsvFrequencySweepExportPort(base_output_dir=Path(self._tmp.name), clock=lambda: CLOCK)

    def tearDown(self):
        self._tmp.cleanup()

    def _open(self):
        opened = self.port.open_export("background", 42.5)
        self.assertTrue(opened.is_success)
        return Path(opened.value)

    def test_opens_a_dated_folder_named_after_role_and_table_height(self):
        self.assertEqual(self._open().name, "2026-11-12_130000_frequencySweep_background_table42.5mm")

    def test_writes_one_row_per_frequency_and_the_raw_samples(self):
        folder = self._open()
        written = self.port.export(str(folder), RESULT, SAMPLES)

        self.assertTrue(written.is_success)
        lines = (folder / "frequency_response.csv").read_text(encoding="utf-8").splitlines()
        self.assertIn("# table_height_mm,42.5", lines)
        rows = list(csv.DictReader(line for line in lines if not line.startswith("#")))
        self.assertEqual([float(r["frequency_hz"]) for r in rows], list(FREQUENCIES))
        self.assertEqual(rows[0]["reference_phase_offset_deg"], "")  # unknown, never guessed
        with open(folder / "samples.csv", encoding="utf-8") as f:
            samples = list(csv.DictReader(f))
        self.assertEqual(len(samples), 6)
        self.assertRegex(samples[0]["timestamp"], r"[+-]\d\d:\d\d$")
        self.assertEqual([f.name for f in written.value], ["frequency_response.csv", "samples.csv"])

    def test_every_written_column_is_described_in_the_parameters(self):
        folder = self._open()
        self.port.export(str(folder), RESULT, SAMPLES)
        for name in ("frequency_response.csv", "samples.csv"):
            header = next(line for line in (folder / name).read_text(encoding="utf-8").splitlines() if not line.startswith("#"))
            for column in header.split(","):
                with self.subTest(file=name, column=column):
                    self.assertIn(column, COLUMNS)

    def test_writes_the_acquisition_parameters_json(self):
        folder = self._open()
        self.assertTrue(self.port.write_acquisition_parameters(str(folder), PARAMETERS).is_success)
        document = json.loads((folder / "acquisition-parameters.json").read_text(encoding="utf-8"))
        self.assertEqual(document["provenance"]["activity"]["id"], "sweep-1")
        self.assertEqual([p.name for p in folder.iterdir()], ["acquisition-parameters.json"])

    def test_unwritable_location_is_a_failure(self):
        blocker = Path(self._tmp.name) / "not_a_dir"
        blocker.write_text("x")
        self.assertTrue(CsvFrequencySweepExportPort(base_output_dir=blocker).open_export("background", 1.0).is_failure)


if __name__ == "__main__":
    unittest.main()
