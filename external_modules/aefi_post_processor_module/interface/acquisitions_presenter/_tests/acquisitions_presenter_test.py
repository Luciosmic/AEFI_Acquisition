"""Le presenter des Acquisitions avec une vue Fake, le vrai catalogue et le vrai service de traitement sur des Fakes."""

import logging

import pytest

from ....application.acquisition_catalog_service.acquisition_catalog_service import AcquisitionCatalogService
from ....application.post_processing_service.dtos.scan_samples_dto import ScanSamplesDTO
from ....application.post_processing_service.post_processing_service import PostProcessingService
from ....domain.acquisition_record.acquisition_record import AcquisitionRecord
from ....domain.acquisition_record.repositories.i_acquisition_repository import IAcquisitionRepository
from ....domain.processing._tests.synthetic_scan_generator import SyntheticScanGenerator
from ....domain.processing.processing_steps.processing_steps import STEP_NAMES, ProcessingParameters
from ....infrastructure.csv_scan_reader.fake.fake_csv_scan_reader import FakeCsvScanReader
from ....infrastructure.hdf5_step_writer.fake.fake_hdf5_step_writer import FakeHdf5StepWriter
from ..acquisitions_presenter import AcquisitionsPresenter

EXPORT = "/export"
OK, OTHER, BROKEN, DONE = "20261112_stepScan_ok", "20261113_flyScan_other", "20261114_stepScan_broken", "20261115_flyScan_done"


class _Signal:
    def __init__(self):
        self._slots = []

    def connect(self, slot):
        self._slots.append(slot)

    def emit(self, *args):
        for slot in self._slots:
            slot(*args)


class FakeAcquisitionsView:
    def __init__(self):
        self.selection_changed = _Signal()
        self.process_selection_requested = _Signal()
        self.process_pending_requested = _Signal()
        self.open_folder_requested = _Signal()
        self.rows = []
        self.opened_folders = []

    def set_rows(self, rows):
        self.rows = list(rows)

    def open_folder(self, path):
        self.opened_folders.append(path)

    def row(self, name):
        return next(row for row in self.rows if row.name == name)


class _Export(IAcquisitionRepository):
    """An export held in memory: processing an acquisition stores its steps file, as the real one does on disk."""

    def __init__(self, names_with_steps):
        self.steps_stored = {name: (name in names_with_steps) for name in (OK, OTHER, BROKEN, DONE)}

    def list_acquisitions(self, export_folder):
        records = []
        for name, kind in sorted((n, "flyScan" if "flyScan" in n else "stepScan") for n in self.steps_stored):
            stored = self.steps_stored[name]
            folder = f"{EXPORT}/{name}"
            records.append(AcquisitionRecord(
                name=name, kind=kind, folder=folder, csv_file=f"{folder}/{name}_aefi.csv",
                acquisition_file=f"{folder}/{name}.h5", csv_modified_at=100.0,
                steps_modified_at=200.0 if stored else None, steps_hold_preprocessed=stored,
            ))
        return records


class _Writer(FakeHdf5StepWriter):
    def __init__(self, export, name):
        super().__init__()
        self._export, self._name = export, name

    def close(self):
        super().close()
        if "preprocessed" in {s.split(" @")[0] for s in self.processing_history()}:
            self._export.steps_stored[self._name] = True


class _Parts:
    """The presenter wired to fakes; `writers` keeps the writer made for each acquisition, `calls` the files processed."""

    def __init__(self, names_with_steps=(DONE,), rotation_angles=(0.0, 0.0, 45.0)):
        generator = SyntheticScanGenerator(grid_size=12, scan_range=10.0)
        data = generator.generate_base_signal()
        channels = ('voltage_x_in_phase', 'voltage_x_quadrature', 'voltage_y_in_phase',
                    'voltage_y_quadrature', 'voltage_z_in_phase', 'voltage_z_quadrature')
        samples = ScanSamplesDTO(x=generator.X.ravel(), y=generator.Y.ravel(), values=data.reshape(-1, 6), channel_names=channels)
        self.reader = FakeCsvScanReader()
        for name in (OK, OTHER, DONE):  # BROKEN has no scan file: its processing fails at the first step
            self.reader.add_file(f"{EXPORT}/{name}/{name}_aefi.csv", samples)
        self.export = _Export(names_with_steps)
        self.catalog = AcquisitionCatalogService(self.export)
        self.writers, self.calls = {}, []
        self.view = FakeAcquisitionsView()
        self.parameters = ProcessingParameters(rotation_angles=rotation_angles)
        self.presenter = AcquisitionsPresenter(
            self.view, self.catalog, self._processor_for, lambda: self.parameters, EXPORT,
        )

    def _processor_for(self, acquisition_file):
        name = acquisition_file.rsplit("/", 1)[1][:-3]
        self.calls.append(name)
        writer = self.writers[name] = _Writer(self.export, name)
        return PostProcessingService(self.reader, writer), writer


@pytest.fixture
def parts():
    return _Parts()


def test_opening_lists_each_acquisition_with_its_type_object_and_state_and_computes_nothing(parts):
    parts.presenter.refresh()

    row = parts.view.row(OK)
    assert (row.kind, row.state, row.detail) == ("pas à pas", "à recalculer", "jamais traitée")
    # The folder name says "ok", the parameters say nothing: the name is never read as the object.
    assert (row.group, row.acquired_at, row.measured_object, row.lift_off) == ("—", "inconnue", "non renseigné", "non renseigné")
    assert parts.view.row(OTHER).kind == "à la volée"
    assert parts.view.row(DONE).state == "traitée"
    assert parts.calls == [] and parts.writers == {}


def test_opening_writes_the_state_of_each_acquisition_in_the_journal(parts, caplog):
    with caplog.at_level(logging.INFO):
        parts.presenter.refresh()

    lines = [r.getMessage() for r in caplog.records if r.getMessage().startswith("acquisition.state ")]
    assert f"acquisition.state scan={OK} state=à recalculer detail=jamais traitée" in lines
    assert f"acquisition.state scan={DONE} state=traitée detail=" in lines
    assert len(lines) == 4
    assert parts.calls == []


def test_an_export_without_acquisition_says_so_in_the_journal(caplog):
    class Empty:
        def list_acquisitions(self, export_folder):
            return []

    view = FakeAcquisitionsView()
    presenter = AcquisitionsPresenter(view, AcquisitionCatalogService(Empty()), None, lambda: None, "/absent")

    with caplog.at_level(logging.WARNING):
        presenter.refresh()

    assert view.rows == []
    assert any(r.levelno == logging.WARNING and r.getMessage().startswith("acquisitions.none_found export=/absent") for r in caplog.records)


def test_choosing_an_acquisition_tells_the_listener_which_one_and_where_its_steps_live(parts):
    chosen = []
    parts.presenter.when_acquisition_chosen(lambda name, file: chosen.append((name, file)))
    parts.presenter.refresh()

    parts.view.selection_changed.emit([OTHER, OK])

    assert chosen == [(OTHER, f"{EXPORT}/{OTHER}/{OTHER}.h5")]


def test_the_process_button_calls_the_service_once_per_acquisition_to_recompute_and_stores_the_five_steps(parts):
    parts.presenter.refresh()

    parts.view.process_pending_requested.emit()

    assert sorted(parts.calls) == sorted([OK, OTHER, BROKEN])  # DONE is up to date
    for name in (OK, OTHER):
        stored = [parts.writers[name].load_step(step) for step in STEP_NAMES]  # read back through the port
        assert len(stored) == 5
    assert parts.view.row(OK).state == "traitée" and parts.view.row(OTHER).state == "traitée"


def test_a_failing_acquisition_does_not_stop_the_next_ones_and_the_balance_names_the_failed_step(parts, caplog):
    parts.presenter.refresh()

    with caplog.at_level(logging.DEBUG):
        parts.view.process_pending_requested.emit()

    row = parts.view.row(BROKEN)
    assert row.state == "en échec" and "étape load_csv" in row.detail and "not found" in row.detail
    assert parts.view.row(OK).state == "traitée" and parts.view.row(OTHER).state == "traitée"  # the ones after BROKEN too
    messages = [r.getMessage() for r in caplog.records]
    assert any(m.startswith(f"scan.failed scan={BROKEN} error_type=FileNotFoundError step=load_csv") for m in messages)
    assert any("rotation_origin=ideal_template" in m and OK in m for m in messages)
    assert f"scan.up_to_date scan={DONE} action=none" in messages
    finished = [r for r in caplog.records if r.getMessage().startswith("sync.finished")]
    assert finished[0].levelno == logging.WARNING
    assert "processed=2 skipped=1 failed=1" in finished[0].getMessage()
    assert f"{BROKEN}:load_csv" in finished[0].getMessage()


def test_a_balance_without_failure_is_an_information(caplog):
    parts = _Parts(names_with_steps=(DONE, BROKEN))
    parts.reader.add_file(f"{EXPORT}/{BROKEN}/{BROKEN}_aefi.csv", parts.reader.read(f"{EXPORT}/{OK}/{OK}_aefi.csv"))
    parts.presenter.refresh()

    with caplog.at_level(logging.INFO):
        parts.presenter.process_pending()

    finished = [r for r in caplog.records if r.getMessage().startswith("sync.finished")]
    assert finished[0].levelno == logging.INFO and "processed=2 skipped=2 failed=0" in finished[0].getMessage()


def test_the_selection_button_processes_the_selected_acquisitions_even_when_up_to_date(parts):
    parts.presenter.refresh()
    parts.view.selection_changed.emit([DONE])

    parts.view.process_selection_requested.emit()

    assert parts.calls == [DONE] and len(parts.writers[DONE].processing_history()) == 5


def test_forcing_processes_every_acquisition(parts):
    parts.presenter.process_pending(force=True)

    assert sorted(parts.calls) == sorted([OK, OTHER, BROKEN, DONE])


def test_a_listener_is_told_when_a_batch_is_over_with_the_new_states_already_shown(parts):
    states_seen = []
    parts.presenter.when_processed(lambda: states_seen.append(parts.view.row(OK).state))
    parts.presenter.refresh()

    parts.presenter.process_pending()

    assert states_seen == ["traitée"]


def test_a_failure_stays_after_the_batch_until_a_success_replaces_it(parts):
    parts.presenter.process_pending()
    assert parts.view.row(BROKEN).state == "en échec"

    parts.reader.add_file(f"{EXPORT}/{BROKEN}/{BROKEN}_aefi.csv", parts.reader.read(f"{EXPORT}/{OK}/{OK}_aefi.csv"))
    parts.view.selection_changed.emit([BROKEN])
    parts.view.process_selection_requested.emit()

    assert parts.view.row(BROKEN).state == "traitée"


def test_opening_the_folder_opens_the_selected_acquisition_or_else_the_export(parts):
    parts.presenter.refresh()

    parts.view.open_folder_requested.emit()
    parts.view.selection_changed.emit([OK])
    parts.view.open_folder_requested.emit()

    assert parts.view.opened_folders == [EXPORT, f"{EXPORT}/{OK}"]


def test_a_row_names_the_group_date_object_and_lift_off_from_the_parameters():
    from dataclasses import replace
    from datetime import datetime, timedelta, timezone

    parts = _Parts()
    listed = parts.export.list_acquisitions
    started = datetime(2026, 11, 13, 20, 40, 52, tzinfo=timezone(timedelta(hours=1)))
    parts.export.list_acquisitions = lambda folder: [
        replace(r, group="WATER", acquired_at=started, measured_object="bouteille_cristalline", lift_off_mm=25.0)
        if r.name == OK else r for r in listed(folder)
    ]

    parts.presenter.refresh()

    row = parts.view.row(OK)
    assert (row.group, row.acquired_at, row.measured_object, row.lift_off) == (
        "WATER", "13/11/2026 20:40", "bouteille_cristalline", "25 mm")
