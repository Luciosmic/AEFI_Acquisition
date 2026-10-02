import json
import re
import unittest
from dataclasses import replace
from datetime import datetime, timezone

from application.services.acquisition_throughput_characterization_service.acquisition_throughput_characterization_service import (
    EXCITATION_CUT,
)
from application.shared.acquisition_parameters.acquisition_conditions_dtos import (
    AcquisitionConditionsDTO,
    BenchPositionDTO,
    SynchronousDetectionStateDTO,
)
from application.services.acquisition_throughput_characterization_service.dtos.acquisition_parameters_dtos import (
    AcquisitionParametersDTO,
)
from infrastructure.acquisition_conditions.fake.fake_acquisition_conditions_port import make_bench_conditions
from infrastructure.persistence.acquisition_throughput._tests import (
    make_acquisition_parameters_dto,
    make_throughput_activity_dto,
)
from infrastructure.persistence.acquisition_throughput.acquisition_parameters_v1_serializer import (
    UCUM_UNITS,
    serialize_acquisition_parameters_v1,
)
from infrastructure.provenance.fake.fake_software_provenance_port import CLEAN, GIT_UNAVAILABLE

ACTIVITY = make_throughput_activity_dto()
PARAMETERS = make_acquisition_parameters_dto()
GENERATED = datetime(2026, 10, 2, 14, 9, 41, tzinfo=timezone.utc)
UCUM_SYNTAX = re.compile(r"^[A-Za-z0-9%/.(){}_\-\[\]]+$")


def serialize(parameters=PARAMETERS):
    return serialize_acquisition_parameters_v1(parameters, GENERATED)


def warning_paths(document):
    return [w["path"] for w in document["warnings"]]


def numbers_outside_quantities(node, path="$", inside_quantity=False):
    """Every number must be a quantity's `value` / `code` (or an element of a list value)."""
    found = []
    if isinstance(node, bool) or node is None or isinstance(node, str):
        return found
    if isinstance(node, (int, float)):
        return [] if inside_quantity else [path]
    if isinstance(node, list):
        for i, item in enumerate(node):
            found += numbers_outside_quantities(item, f"{path}[{i}]", inside_quantity)
        return found
    is_quantity = "unit" in node and ("value" in node or "code" in node)
    for key, value in node.items():
        found += numbers_outside_quantities(value, f"{path}.{key}", is_quantity and key in ("value", "code"))
    return found


def units(node, path="$"):
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "unit":
                yield path, value
            else:
                yield from units(value, f"{path}.{key}")
    elif isinstance(node, list):
        for i, item in enumerate(node):
            yield from units(item, f"{path}[{i}]")


class TestQuantityGuard(unittest.TestCase):
    """Schema 1.0: the unit travels with the value, as a UCUM code."""

    def test_every_number_is_a_quantity_with_a_unit(self):
        document = json.loads(json.dumps(serialize()))
        self.assertEqual(numbers_outside_quantities(document), [])

    def test_every_unit_is_a_known_ucum_code(self):
        found = list(units(serialize()))
        self.assertTrue(found)
        for path, unit in found:
            with self.subTest(path=path):
                self.assertIn(unit, UCUM_UNITS)
                self.assertRegex(unit, UCUM_SYNTAX)

    def test_the_guard_catches_a_bare_number(self):
        self.assertEqual(numbers_outside_quantities({"a": {"b": 3}}), ["$.a.b"])
        self.assertEqual(numbers_outside_quantities({"a": {"value": 3, "unit": "s"}}), [])

    def test_unknown_catalog_unit_is_annotated_and_warned(self):
        conditions = make_bench_conditions()
        sensor = replace(conditions.components[0], units={"transduction_gain_v_per_v_per_m": "furlong"})
        document = serialize(replace(PARAMETERS, conditions=replace(conditions, components=(sensor,))))
        gain = document["components"]["sensor"]["characterization"]["transduction_gain_v_per_v_per_m"]
        self.assertEqual(gain["unit"], "{furlong}")
        self.assertIn("components.sensor.characterization.transduction_gain_v_per_v_per_m", warning_paths(document))


class TestAcquisitionParametersV1(unittest.TestCase):
    def setUp(self):
        self.document = serialize()

    def test_schema_and_prov_activity(self):
        self.assertEqual(self.document["schema"], {"name": "aefi-acquisition-parameters", "version": "1.0"})
        activity = self.document["provenance"]["activity"]
        self.assertEqual(activity["kind"], "mcu_throughput_characterization")
        self.assertEqual(activity["status"], "completed")
        self.assertRegex(activity["started_at"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}[+-]\d\d:\d\d$")
        self.assertIsNotNone(activity["ended_at"])
        self.assertEqual(activity["exclusive_control"]["held"][1], "acquisition_stream")
        self.assertEqual(self.document["provenance"]["software"]["commit"], CLEAN.commit)
        self.assertIsNone(self.document["provenance"]["operator"]["name"])
        self.assertIn("provenance.operator.name", warning_paths(self.document))

    def test_no_feature_of_interest_is_stated_not_omitted(self):
        self.assertIs(self.document["feature_of_interest"]["present"], False)

    def test_procedure(self):
        procedure = self.document["procedure"]["mcu_throughput_characterization"]
        self.assertEqual(procedure["n_avg_grid"], {"value": [1, 8, 127], "unit": "{sample}"})
        self.assertEqual(procedure["settle_delay"], {"value": 0.5, "unit": "s"})
        self.assertEqual(procedure["excitation"], "cut")

    def test_components_once_each_with_applied_settings(self):
        components = self.document["components"]
        self.assertEqual(components["adc"]["component"]["id"], "e-adc")
        self.assertEqual(components["adc"]["settings"]["oversampling_ratio"], {"value": 4096, "unit": "1"})
        self.assertEqual(components["adc"]["settings"]["channels"]["8"]["digital_gain"], {"value": 1, "unit": "1"})
        channel_3 = components["signal_generation_chip"]["settings"]["channels"]["3"]
        self.assertEqual(channel_3["phase"], {"code": 16384, "value": 90.0, "unit": "deg"})
        self.assertEqual(components["signal_generation_chip"]["settings"]["channels"]["1"]["digital_gain"]["code"], 0)
        link = components["microcontroller"]["settings"]["host_link"]
        self.assertEqual(link["usb_latency_timer"], {"value": 1.0, "unit": "ms"})
        self.assertEqual(link["serial_port"], "COM10")
        self.assertIsNone(components["adc"]["characterization"]["noise_v_rms"])
        self.assertIn("components.adc.characterization.noise_v_rms", warning_paths(self.document))

    def test_rate_curve_is_abscissa_and_ordinate(self):
        curve = self.document["components"]["microcontroller"]["characterization"]["optimal_acquisition_rate_per_s"]
        self.assertEqual(curve["abscissa"], {"name": "n_avg", "value": [1, 8, 127], "unit": "{sample}"})
        self.assertEqual(curve["ordinate"]["unit"], "{sample}/s")

    def test_measurement_chain_states_the_cut_the_reference_and_the_stream(self):
        chain = self.document["measurement_chain"]
        self.assertEqual(chain["excitation"]["state"]["applied"], "cut")
        self.assertEqual(chain["excitation"]["state"]["definition"], EXCITATION_CUT.definition)
        self.assertEqual(chain["excitation"]["state"]["operator_setting"]["level_s1_s2"], {"value": 20.0, "unit": "%"})
        detection = chain["synchronous_detection"]["state"]
        self.assertIs(detection["lock_in_enabled"], True)
        self.assertEqual(detection["phase_offset"], {"value": 0.0, "unit": "deg"})
        self.assertEqual(chain["digitization"]["stream"]["origin"], "started_by_activity")
        self.assertEqual(chain["positioning"]["state"]["position_at_start"]["x"], {"value": 12.5, "unit": "mm"})
        self.assertEqual(chain["sensor"]["deployment"]["rotation_applied"]["origin"], "ideal")
        self.assertIn("measurement_chain.sensor.deployment.rotation_applied.origin", warning_paths(self.document))

    def test_generated_files_with_their_checksum(self):
        files = self.document["data"]["files"]
        self.assertEqual([f["name"] for f in files], ["summary.csv", "samples.csv", "acquisition-parameters.json"])
        self.assertEqual(files[0]["byte_size"], {"value": 1234, "unit": "By"})
        self.assertEqual(files[1]["sha256"], "b" * 64)

    def test_running_document_warns_it_is_unfinished(self):
        running = replace(ACTIVITY, status="running", ended_at=None, n_avg_restored=None, bench_position_end=None)
        document = serialize(replace(PARAMETERS, activity=running, files=()))
        self.assertIsNone(document["provenance"]["activity"]["ended_at"])
        self.assertIn("provenance.activity.ended_at", warning_paths(document))
        self.assertNotIn("provenance.activity.ended_at", warning_paths(self.document))

    def test_every_unknown_is_a_warning(self):
        activity = replace(
            ACTIVITY, usb_latency_timer_ms=None, usb_latency_unknown_reason="registre FTDI illisible",
            bench_position_start=None, bench_position_end=None, bench_position_unknown_reason="moteurs non connectés",
            n_avg_restored=False,
        )
        conditions = AcquisitionConditionsDTO(
            unknown={"components": "OSError: disque", "adc": "LookupError", "signal_generation": "KeyError: DDS",
                     "sensor_deployment": "RuntimeError", "synchronous_detection": "AttributeError"},
            hardware_backends={"aefi_device": "mock", "motion": "real"},
        )
        document = serialize(AcquisitionParametersDTO(activity, conditions, GIT_UNAVAILABLE, ()))
        paths = warning_paths(document)
        for expected in (
            "provenance.software.commit", "provenance.software.dirty", "provenance.software.hardware_backends",
            "components", "components.adc.settings", "components.signal_generation_chip.settings",
            "components.microcontroller.settings.host_link.serial_port",
            "components.microcontroller.settings.host_link.usb_latency_timer",
            "components.microcontroller.settings.n_avg_before_activity",
            "measurement_chain.sensor.deployment", "measurement_chain.synchronous_detection.state",
            "measurement_chain.positioning.state.position_at_start",
        ):
            self.assertIn(expected, paths)
        latency_warning = next(w for w in document["warnings"] if w["path"].endswith("usb_latency_timer"))
        self.assertIn("registre FTDI illisible", latency_warning["message"])
        self.assertEqual(numbers_outside_quantities(document), [])

    def test_compensation_without_identified_calibration_is_warned(self):
        conditions = replace(make_bench_conditions(), synchronous_detection=SynchronousDetectionStateDTO(True))
        document = serialize(replace(PARAMETERS, conditions=conditions))
        self.assertIn("measurement_chain.synchronous_detection.state.phase_calibration_id", warning_paths(document))

    def test_bench_moved_during_the_sweep_is_warned(self):
        moved = replace(ACTIVITY, bench_position_end=BenchPositionDTO(12.5, 0.0))
        self.assertIn("measurement_chain.positioning.state", warning_paths(serialize(replace(PARAMETERS, activity=moved))))


if __name__ == "__main__":
    unittest.main()
