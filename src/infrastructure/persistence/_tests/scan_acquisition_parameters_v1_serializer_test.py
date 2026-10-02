import json
import unittest
from datetime import datetime, timezone

from application.services.scan_export_service.dtos.scan_acquisition_parameters_dtos import (
    TIME_SERIES,
    ElectricFieldProbeDTO,
)
from application.shared.acquisition_parameters.acquisition_conditions_dtos import BenchPositionDTO
from infrastructure.persistence._tests import make_scan_acquisition_parameters
from infrastructure.persistence.acquisition_parameters.acquisition_parameters_v1 import UCUM_UNITS
from infrastructure.persistence.scan_acquisition_parameters_v1_serializer import (
    STEP_SCAN_COLUMNS,
    TIME_SERIES_COLUMNS,
    serialize_scan_acquisition_parameters_v1,
)

GENERATED = datetime(2026, 10, 2, 14, 9, 41, tzinfo=timezone.utc)


def serialize(parameters):
    return serialize_scan_acquisition_parameters_v1(parameters, GENERATED)


def units(node):
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "unit" and isinstance(value, str):
                yield value
            else:
                yield from units(value)
    elif isinstance(node, list):
        for item in node:
            yield from units(item)


def warning_paths(document):
    return [w["path"] for w in document["warnings"]]


class TestScanAcquisitionParametersV1Serializer(unittest.TestCase):
    def test_step_scan_document_has_every_schema_section_and_is_plain_json(self):
        document = serialize(make_scan_acquisition_parameters(ended=True))
        self.assertEqual(
            list(document),
            ["schema", "provenance", "feature_of_interest", "procedure", "components", "measurement_chain", "data", "warnings"],
        )
        json.dumps(document)  # no custom encoder needed

    def test_document_units_are_declared_ucum_codes(self):
        document = serialize(make_scan_acquisition_parameters(ended=True))
        column_units = {c["unit"] for c in document["data"]["columns"].values() if "unit" in c}
        self.assertEqual(set(units(document)) - column_units - UCUM_UNITS, set())

    def test_procedure_carries_what_was_asked_with_units(self):
        procedure = serialize(make_scan_acquisition_parameters())["procedure"]["step_scan"]
        self.assertEqual(procedure["zone"]["x_min"], {"value": 435.0, "unit": "mm"})
        self.assertEqual(procedure["averaging_per_position"], {"value": 10, "unit": "{sample}"})
        self.assertEqual(procedure["differential"]["enabled"], False)
        self.assertEqual(procedure["measurement_uncertainty"], {"value": 1e-6, "unit": "V"})

    def test_reproducibility_settings_are_present(self):
        components = serialize(make_scan_acquisition_parameters())["components"]
        self.assertEqual(components["microcontroller"]["settings"]["n_avg"], {"value": 127, "unit": "{sample}"})
        self.assertEqual(components["adc"]["settings"]["oversampling_ratio"], {"value": 4096, "unit": "1"})
        self.assertEqual(components["motors"]["settings"]["step_size"], {"value": 21.8, "unit": "um/{step}"})
        self.assertEqual(components["microcontroller"]["settings"]["host_link"]["usb_latency_timer"], {"value": 1.0, "unit": "ms"})

    def test_exported_voltages_are_declared_in_the_sensor_frame(self):
        deployment = serialize(make_scan_acquisition_parameters())["measurement_chain"]["sensor"]["deployment"]
        self.assertFalse(deployment["rotation_applied"]["applies_to_data"])
        self.assertEqual(STEP_SCAN_COLUMNS["voltage_x_in_phase"]["frame"], "sensor")

    def test_undescribed_measured_object_is_a_warning(self):
        document = serialize(make_scan_acquisition_parameters())
        self.assertTrue(document["feature_of_interest"]["present"])
        self.assertIn("feature_of_interest.description", warning_paths(document))

    def test_a_running_document_says_so_and_the_final_one_does_not(self):
        self.assertIn("provenance.activity.ended_at", warning_paths(serialize(make_scan_acquisition_parameters())))
        self.assertNotIn("provenance.activity.ended_at", warning_paths(serialize(make_scan_acquisition_parameters(ended=True))))

    def test_step_scan_moves_the_bench_without_a_warning(self):
        positioning = serialize(make_scan_acquisition_parameters(ended=True))["measurement_chain"]["positioning"]["state"]
        self.assertTrue(positioning["motors_held_by_activity"])
        self.assertEqual(positioning["position_at_end"]["x"], {"value": 835.0, "unit": "mm"})

    def test_time_series_has_its_own_columns_and_warns_if_the_bench_moved(self):
        document = serialize(make_scan_acquisition_parameters(TIME_SERIES, ended=True))
        self.assertEqual(document["procedure"], {"time_series": {}})
        self.assertEqual(set(document["data"]["columns"]), set(TIME_SERIES_COLUMNS))
        self.assertIn("measurement_chain.positioning.state", warning_paths(document))

    def test_connected_probe_is_a_component_and_an_absent_one_is_noted_not_unknown(self):
        absent = serialize(make_scan_acquisition_parameters())
        self.assertEqual(absent["measurement_chain"]["auxiliary_probes"]["uses"], [])
        self.assertNotIn("components.electric_field_probe", " ".join(warning_paths(absent)))

        probe = ElectricFieldProbeDTO("Narda", "EP-601", "SN123", ("x", "y", "z"), battery_percentage=62.0)
        present = serialize(make_scan_acquisition_parameters(probe=probe))
        self.assertEqual(present["components"]["electric_field_probe"]["component"]["serial_number"], "SN123")
        self.assertEqual(present["components"]["electric_field_probe"]["state"]["battery_percentage"], {"value": 62.0, "unit": "%"})


if __name__ == "__main__":
    unittest.main()
