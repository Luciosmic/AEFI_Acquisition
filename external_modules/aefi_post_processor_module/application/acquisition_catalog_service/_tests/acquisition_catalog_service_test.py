import pytest

from ....domain.acquisition_record.acquisition_record import AcquisitionRecord
from ....infrastructure.export_folder_repository.fake.fake_export_folder_repository import FakeExportFolderRepository
from ..acquisition_catalog_service import AcquisitionCatalogService
from ..dtos.acquisition_outcome_dto import AcquisitionOutcomeDTO
from ..dtos.acquisition_status_dto import FAILED, PROCESSED, TO_RECOMPUTE
from ..dtos.list_acquisitions_dto import ListAcquisitionsDTO

EXPORT = "/export"


def _record(name, csv_time, steps_time):
    folder = f"{EXPORT}/{name}"
    return AcquisitionRecord(
        name=name, kind="stepScan", folder=folder, csv_file=f"{folder}/{name}_aefi.csv",
        acquisition_file=f"{folder}/{name}.h5", csv_modified_at=csv_time, steps_modified_at=steps_time,
    )


@pytest.fixture
def repository():
    repository = FakeExportFolderRepository()
    repository.add(EXPORT, _record("20261112_stepScan_new", 100.0, None))
    repository.add(EXPORT, _record("20261113_stepScan_done", 100.0, 200.0))
    repository.add(EXPORT, _record("20261114_stepScan_touched", 300.0, 200.0))
    return repository


def _states(service, force=False):
    return {s.name: s for s in service.list_acquisitions(ListAcquisitionsDTO(EXPORT, force))}


def test_each_acquisition_is_processed_or_to_recompute_with_its_reason(repository):
    statuses = _states(AcquisitionCatalogService(repository))

    assert statuses["20261112_stepScan_new"].state == TO_RECOMPUTE and statuses["20261112_stepScan_new"].reason == "new"
    assert statuses["20261113_stepScan_done"].state == PROCESSED and statuses["20261113_stepScan_done"].reason is None
    assert statuses["20261114_stepScan_touched"].state == TO_RECOMPUTE
    assert statuses["20261114_stepScan_touched"].reason == "source_newer"


def test_forcing_makes_a_processed_acquisition_to_recompute(repository):
    statuses = _states(AcquisitionCatalogService(repository), force=True)

    assert statuses["20261113_stepScan_done"].state == TO_RECOMPUTE and statuses["20261113_stepScan_done"].reason == "forced"


def test_a_failure_is_kept_with_its_message_until_a_success_is_reported(repository):
    service = AcquisitionCatalogService(repository)

    service.report_outcome(AcquisitionOutcomeDTO("20261112_stepScan_new", False, "malformed CSV"))
    failed = _states(service)["20261112_stepScan_new"]
    assert failed.state == FAILED and failed.failure_message == "malformed CSV" and failed.reason is None

    service.report_outcome(AcquisitionOutcomeDTO("20261112_stepScan_new", True))
    assert _states(service)["20261112_stepScan_new"].state == TO_RECOMPUTE


def test_an_unknown_export_folder_lists_nothing(repository):
    service = AcquisitionCatalogService(repository)

    assert service.list_acquisitions(ListAcquisitionsDTO("/elsewhere")) == ()
