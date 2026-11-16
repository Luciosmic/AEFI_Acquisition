from ..acquisition_record import FORCED, NEW, SOURCE_NEWER, AcquisitionRecord


def _record(csv_modified_at=100.0, steps_modified_at=None):
    return AcquisitionRecord(
        name="20261112_stepScan_a", kind="stepScan", folder="/export/20261112_stepScan_a",
        csv_file="/export/20261112_stepScan_a/a_aefi.csv", acquisition_file="/export/20261112_stepScan_a/20261112_stepScan_a.h5",
        csv_modified_at=csv_modified_at, steps_modified_at=steps_modified_at,
    )


def test_an_acquisition_without_steps_file_is_new():
    assert _record().recalculation_reason() == NEW


def test_steps_newer_than_the_scan_file_are_up_to_date():
    record = _record(csv_modified_at=100.0, steps_modified_at=200.0)

    assert record.recalculation_reason() is None and not record.needs_recalculation()


def test_a_scan_file_touched_after_the_steps_makes_them_stale():
    record = _record(csv_modified_at=300.0, steps_modified_at=200.0)

    assert record.recalculation_reason() == SOURCE_NEWER and record.needs_recalculation()


def test_a_scan_file_as_old_as_the_steps_makes_them_stale():
    assert _record(csv_modified_at=200.0, steps_modified_at=200.0).recalculation_reason() == SOURCE_NEWER


def test_forcing_recalculates_up_to_date_steps():
    record = _record(csv_modified_at=100.0, steps_modified_at=200.0)

    assert record.recalculation_reason(forced=True) == FORCED


def test_a_new_acquisition_stays_new_when_forced():
    assert _record().recalculation_reason(forced=True) == NEW
