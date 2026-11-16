"""Suite de contrat du port IStepWriter : passée par l'adaptateur réel et par son Fake."""

import numpy as np
import pytest

STEPS = ('preprocessed', 'phase_calibrated')


class StepWriterContract:
    """Hérité par une classe de test qui fournit `make_writer()` : un écrivain neuf, lié à une acquisition vide."""

    def make_writer(self):
        raise NotImplementedError

    def test_a_step_written_is_read_back_with_the_same_values_nan_included(self):
        writer = self.make_writer()
        data = np.array([[[1.0, np.nan], [3.5, -2.0]]])

        writer.save_step('preprocessed', data, {'grid_size': 2})
        read, _ = writer.load_step('preprocessed')

        assert np.array_equal(read, data, equal_nan=True)

    def test_scalar_metadata_is_read_back_equal(self):
        writer = self.make_writer()

        writer.save_step('preprocessed', np.zeros((1, 1, 1)), {'grid_size': 4, 'x_step': 0.25, 'method': 'cubic'})
        _, metadata = writer.load_step('preprocessed')

        assert (metadata['grid_size'], metadata['x_step'], metadata['method']) == (4, 0.25, 'cubic')

    def test_saving_a_step_again_replaces_it(self):
        writer = self.make_writer()

        writer.save_step('preprocessed', np.zeros((1, 1, 1)), {})
        writer.save_step('preprocessed', np.ones((2, 2, 1)), {})
        read, _ = writer.load_step('preprocessed')

        assert read.shape == (2, 2, 1) and read.sum() == 4.0

    def test_the_history_lists_the_steps_in_the_order_they_were_saved(self):
        writer = self.make_writer()

        for step in STEPS:
            writer.save_step(step, np.zeros((1, 1, 1)), {})

        assert [entry.split(' @ ')[0] for entry in writer.processing_history()] == list(STEPS)

    def test_a_step_never_saved_is_refused(self):
        writer = self.make_writer()

        with pytest.raises(KeyError):
            writer.load_step('interpolated')
