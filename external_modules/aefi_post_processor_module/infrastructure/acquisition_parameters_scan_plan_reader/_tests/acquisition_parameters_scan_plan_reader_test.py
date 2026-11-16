import json

import pytest

from ....domain.processing.planned_scan_grid.planned_scan_grid import PlannedScanGrid
from ..acquisition_parameters_scan_plan_reader import AcquisitionParametersScanPlanReader
from .scan_plan_reader_contract import PLAN, ScanPlanReaderContract


def _description(plan: PlannedScanGrid, unit: str = 'mm') -> dict:
    """The part of an acquisition parameters file (schema 1.4) that holds the planned grid."""

    def bound(value):
        return {'value': value, 'unit': unit}

    return {
        'schema': {'name': 'aefi-acquisition-parameters', 'version': '1.4'},
        'procedure': {'step_scan': {
            'zone': {'x_min': bound(plan.x.minimum), 'x_max': bound(plan.x.maximum),
                     'y_min': bound(plan.y.minimum), 'y_max': bound(plan.y.maximum)},
            'grid': {'x_nb_points': plan.x.points, 'y_nb_points': plan.y.points,
                     'total_points': plan.x.points * plan.y.points},
            'pattern': 'SERPENTINE',
        }},
    }


class TestAcquisitionParametersScanPlanReader(ScanPlanReaderContract):
    @pytest.fixture(autouse=True)
    def _folder(self, tmp_path):
        self.folder = tmp_path

    def path_of(self, name):
        return str(self.folder / name)

    def _write(self, csv_name: str, content: str) -> None:
        parameters = csv_name.replace('_aefi.csv', '_acquisition-parameters.json')
        (self.folder / parameters).write_text(content, encoding='utf-8')

    def reader_describing(self, name, plan):
        self._write(name, json.dumps(_description(plan)))
        return AcquisitionParametersScanPlanReader()

    def reader_describing_nothing(self):
        return AcquisitionParametersScanPlanReader()

    def test_a_csv_the_acquisition_did_not_name_has_no_planned_grid(self):
        assert AcquisitionParametersScanPlanReader().planned_grid(self.path_of("scan_001_baseline.csv")) is None

    def test_an_unreadable_description_gives_no_planned_grid(self):
        self._write("c_aefi.csv", "{ not json")

        assert AcquisitionParametersScanPlanReader().planned_grid(self.path_of("c_aefi.csv")) is None

    def test_a_description_without_grid_gives_no_planned_grid(self):
        self._write("d_aefi.csv", json.dumps({'procedure': {'frequency_sweep': {}}}))

        assert AcquisitionParametersScanPlanReader().planned_grid(self.path_of("d_aefi.csv")) is None

    def test_bounds_in_another_unit_than_the_csv_give_no_planned_grid(self):
        self._write("e_aefi.csv", json.dumps(_description(PLAN, unit='m')))

        assert AcquisitionParametersScanPlanReader().planned_grid(self.path_of("e_aefi.csv")) is None

    def test_a_description_with_accents_is_read_as_utf8(self):
        description = _description(PLAN)
        description['feature_of_interest'] = {'description': "bouteille d’eau déionisée"}
        self._write("f_aefi.csv", json.dumps(description, ensure_ascii=False))

        assert AcquisitionParametersScanPlanReader().planned_grid(self.path_of("f_aefi.csv")) == PLAN
