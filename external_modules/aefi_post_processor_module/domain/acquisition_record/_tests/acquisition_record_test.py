from ..acquisition_record import FORCED, INCOMPLETE, NEW, SOURCE_NEWER, AcquisitionRecord


def _record(csv_modified_at=100.0, steps_modified_at=None, steps_hold_preprocessed=True):
    return AcquisitionRecord(
        name="20261112_stepScan_a", kind="stepScan", folder="/export/20261112_stepScan_a",
        csv_file="/export/20261112_stepScan_a/a_aefi.csv", acquisition_file="/export/20261112_stepScan_a/20261112_stepScan_a.h5",
        csv_modified_at=csv_modified_at, steps_modified_at=steps_modified_at,
        steps_hold_preprocessed=steps_hold_preprocessed,
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


def test_a_steps_file_without_the_first_step_is_incomplete_even_when_newer_than_the_scan_file():
    record = _record(csv_modified_at=100.0, steps_modified_at=200.0, steps_hold_preprocessed=False)

    assert record.recalculation_reason() == INCOMPLETE and record.needs_recalculation()


def test_an_incomplete_steps_file_stays_incomplete_when_forced():
    record = _record(csv_modified_at=100.0, steps_modified_at=200.0, steps_hold_preprocessed=False)

    assert record.recalculation_reason(forced=True) == INCOMPLETE


def test_a_missing_steps_file_is_new_not_incomplete():
    assert _record(steps_modified_at=None, steps_hold_preprocessed=False).recalculation_reason() == NEW
