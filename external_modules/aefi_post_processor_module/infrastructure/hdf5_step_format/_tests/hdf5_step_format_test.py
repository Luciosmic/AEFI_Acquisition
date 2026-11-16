from ..hdf5_step_format import processing_store_path, step_group_name


def test_steps_are_stored_in_the_file_of_the_acquisition():
    assert processing_store_path("/scans/20261112_stepScan_a/a.h5") == "/scans/20261112_stepScan_a/a.h5"


def test_a_step_is_a_group_at_the_root_named_after_it():
    assert step_group_name("phase_calibrated") == "/phase_calibrated"
