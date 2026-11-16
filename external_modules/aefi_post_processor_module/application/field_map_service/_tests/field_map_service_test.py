import json

import numpy as np
import pytest

from ....infrastructure.hdf5_step_reader.fake.fake_hdf5_step_reader import FakeHdf5StepReader
from ..dtos.load_step_dto import LoadStepDTO
from ..dtos.steps_request_dto import StepsRequestDTO
from ..field_map_service import FieldMapService

FILE = "/export/a/a.h5"
DATA = np.arange(2 * 2 * 6, dtype=float).reshape(2, 2, 6)
CHANNELS = ['voltage_x_in_phase', 'voltage_x_quadrature', 'voltage_y_in_phase',
            'voltage_y_quadrature', 'voltage_z_in_phase', 'voltage_z_quadrature']


@pytest.fixture
def reader():
    reader = FakeHdf5StepReader()
    for name in ("interpolated", "preprocessed", "phase_calibrated"):  # not in processing order
        reader.add_step(FILE, name, DATA, {'channel_names': json.dumps(CHANNELS), 'extent': np.array([0.0, 2.0, 1.0, 3.0])})
    return reader


def test_steps_are_listed_in_processing_order(reader):
    assert FieldMapService(reader).list_steps(StepsRequestDTO(FILE)) == ("preprocessed", "phase_calibrated", "interpolated")


def test_an_acquisition_without_steps_lists_none(reader):
    assert FieldMapService(reader).list_steps(StepsRequestDTO("/export/b/b.h5")) == ()


def test_a_step_gives_one_grid_per_channel_and_its_extent(reader):
    field_map = FieldMapService(reader).load_step(LoadStepDTO(FILE, "preprocessed"))

    assert list(field_map.grids) == CHANNELS
    assert np.array_equal(field_map.grids['voltage_z_quadrature'], DATA[:, :, 5])
    assert field_map.extent == (0.0, 2.0, 1.0, 3.0) and field_map.step_name == "preprocessed"


def test_missing_channel_names_fall_back_to_the_six_voltage_channels():
    reader = FakeHdf5StepReader()
    reader.add_step(FILE, "preprocessed", DATA, {})

    field_map = FieldMapService(reader).load_step(LoadStepDTO(FILE, "preprocessed"))

    assert list(field_map.grids) == CHANNELS and field_map.extent == (0.0, 1.0, 0.0, 1.0)


def test_channel_names_that_do_not_match_the_data_fall_back_too():
    reader = FakeHdf5StepReader()
    reader.add_step(FILE, "preprocessed", DATA, {'channel_names': json.dumps(['only_one'])})

    assert list(FieldMapService(reader).load_step(LoadStepDTO(FILE, "preprocessed")).grids) == CHANNELS


def test_a_step_never_stored_is_refused(reader):
    with pytest.raises(KeyError):
        FieldMapService(reader).load_step(LoadStepDTO(FILE, "rotated_frame"))
