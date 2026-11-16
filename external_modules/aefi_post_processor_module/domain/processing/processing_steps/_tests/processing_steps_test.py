import dataclasses

import pytest

from ...processing_steps.processing_steps import (
    STEP_NAMES,
    ProcessingParameters,
    step_index,
)


def test_steps_are_the_five_closed_names_in_processing_order():
    assert STEP_NAMES == ('preprocessed', 'phase_calibrated', 'amplitude_subtracted', 'rotated_frame', 'interpolated')


def test_step_index_follows_the_order_and_refuses_an_unknown_name():
    assert [step_index(name) for name in STEP_NAMES] == [0, 1, 2, 3, 4]
    with pytest.raises(ValueError):
        step_index('denoised')


def test_default_parameters_are_those_of_the_pipeline():
    params = ProcessingParameters()

    assert (params.border_width, params.interpolation_method, params.target_grid_size) == (1, 'cubic', None)
    assert params.reference_point == (0, 0) and params.rotation_angles is None


def test_parameters_are_frozen():
    params = ProcessingParameters(rotation_angles=(0.0, 0.0, 45.0))

    with pytest.raises(dataclasses.FrozenInstanceError):
        params.border_width = 2  # type: ignore[misc]
