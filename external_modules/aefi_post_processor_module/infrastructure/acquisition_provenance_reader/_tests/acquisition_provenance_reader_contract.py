"""Suite de contrat du port IAcquisitionProvenanceReader : passée par l'adaptateur réel et par son Fake."""

from ....application.post_processing_service.dtos.acquisition_provenance_dto import AcquisitionProvenanceDTO

PROVENANCE = AcquisitionProvenanceDTO(activity_id="9f1c0a52-7d3e-4c0e-9d57-2b1f6a3e8c11", declared_csv_sha256="ab" * 32)


class AcquisitionProvenanceReaderContract:
    """Hérité par une classe de test qui fournit `path_of(name)`, `reader_describing(name, provenance)` et `reader_describing_nothing()`."""

    def path_of(self, name: str) -> str:
        raise NotImplementedError

    def reader_describing(self, name: str, provenance: AcquisitionProvenanceDTO):
        raise NotImplementedError

    def reader_describing_nothing(self):
        raise NotImplementedError

    def test_a_described_scan_gives_back_its_activity_and_the_hash_its_acquisition_recorded(self):
        reader = self.reader_describing("a_aefi.csv", PROVENANCE)

        assert reader.read(self.path_of("a_aefi.csv")) == PROVENANCE

    def test_a_scan_without_description_has_no_provenance(self):
        assert self.reader_describing_nothing().read(self.path_of("b_aefi.csv")) is None
