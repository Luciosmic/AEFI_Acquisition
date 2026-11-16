"""Suite de contrat du port IScanPlanReader : passée par l'adaptateur réel et par son Fake."""

from ....domain.processing.planned_scan_grid.planned_scan_grid import PlannedAxis, PlannedScanGrid

PLAN = PlannedScanGrid(x=PlannedAxis(300.38223, 900.38223, 150), y=PlannedAxis(380.92726, 780.92726, 100))


class ScanPlanReaderContract:
    """Hérité par une classe de test qui fournit `path_of(name)`, `reader_describing(name, plan)` et `reader_describing_nothing()`."""

    def path_of(self, name: str) -> str:
        raise NotImplementedError

    def reader_describing(self, name: str, plan: PlannedScanGrid):
        raise NotImplementedError

    def reader_describing_nothing(self):
        raise NotImplementedError

    def test_a_described_scan_gives_back_its_planned_grid(self):
        reader = self.reader_describing("a_aefi.csv", PLAN)

        assert reader.planned_grid(self.path_of("a_aefi.csv")) == PLAN

    def test_a_scan_without_description_has_no_planned_grid(self):
        assert self.reader_describing_nothing().planned_grid(self.path_of("b_aefi.csv")) is None
