import json

import pytest

from ....application.post_processing_service.dtos.acquisition_provenance_dto import AcquisitionProvenanceDTO
from ..acquisition_provenance_reader import AcquisitionProvenanceReader
from .acquisition_provenance_reader_contract import PROVENANCE, AcquisitionProvenanceReaderContract


def _description(provenance: AcquisitionProvenanceDTO, csv_name: str) -> dict:
    """The parts of an acquisition parameters file (schema 1.6) that hold the activity id and the hashed files."""
    return {
        'schema': {'name': 'aefi-acquisition-parameters', 'version': '1.6'},
        'provenance': {'activity': {'id': provenance.activity_id, 'kind': 'step_scan', 'status': 'completed'}},
        'data': {'files': [
            {'name': 'a_logs.log.xz', 'format': 'text (xz)', 'sha256': 'cd' * 32},
            {'name': csv_name, 'format': 'CSV', 'sha256': provenance.declared_csv_sha256},
            {'name': 'a_acquisition-parameters.json', 'format': 'JSON'},
        ]},
    }


class TestAcquisitionProvenanceReader(AcquisitionProvenanceReaderContract):
    @pytest.fixture(autouse=True)
    def _folder(self, tmp_path):
        self.folder = tmp_path

    def path_of(self, name):
        return str(self.folder / name)

    def _write(self, csv_name, content):
        (self.folder / csv_name.replace('_aefi.csv', '_acquisition-parameters.json')).write_text(content, encoding='utf-8')

    def reader_describing(self, name, provenance):
        self._write(name, json.dumps(_description(provenance, name)))
        return AcquisitionProvenanceReader()

    def reader_describing_nothing(self):
        return AcquisitionProvenanceReader()

    def test_a_csv_the_acquisition_did_not_name_has_no_provenance(self):
        assert AcquisitionProvenanceReader().read(self.path_of("scan_001_baseline.csv")) is None

    def test_an_unreadable_description_gives_no_provenance(self):
        self._write("a_aefi.csv", "{ not json")

        assert AcquisitionProvenanceReader().read(self.path_of("a_aefi.csv")) is None

    def test_a_description_that_does_not_list_the_csv_gives_the_activity_without_a_hash(self):
        description = _description(PROVENANCE, "a_aefi.csv")
        description['data']['files'] = []
        self._write("a_aefi.csv", json.dumps(description))

        read = AcquisitionProvenanceReader().read(self.path_of("a_aefi.csv"))

        assert read == AcquisitionProvenanceDTO(activity_id=PROVENANCE.activity_id, declared_csv_sha256=None)

    def test_a_description_without_activity_id_gives_the_hash_alone(self):
        description = _description(PROVENANCE, "a_aefi.csv")
        del description['provenance']
        self._write("a_aefi.csv", json.dumps(description))

        read = AcquisitionProvenanceReader().read(self.path_of("a_aefi.csv"))

        assert read == AcquisitionProvenanceDTO(activity_id=None, declared_csv_sha256=PROVENANCE.declared_csv_sha256)
