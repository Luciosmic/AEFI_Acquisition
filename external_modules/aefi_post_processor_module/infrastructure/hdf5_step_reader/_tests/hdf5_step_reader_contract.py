"""Suite de contrat du port IStepReader : passée par l'adaptateur réel et par son Fake."""

import numpy as np
import pytest

CHANNEL_DATA = np.arange(2 * 2 * 3, dtype=float).reshape(2, 2, 3)


class StepReaderContract:
    """
    Hérité par une classe de test qui fournit :
    - `acquisition_file` : la chaîne du fichier d'acquisition ;
    - `reader_holding(steps)` : un lecteur dont ce fichier contient `steps`, un dict `{nom d'étape: (données, métadonnées)}`
      (vide : le fichier n'existe pas ; `{'preprocessed': ...}` : il existe avec cette étape).
    """

    acquisition_file: str

    def reader_holding(self, steps):
        raise NotImplementedError

    def test_the_steps_of_the_file_are_listed(self):
        reader = self.reader_holding({'preprocessed': (CHANNEL_DATA, {}), 'phase_calibrated': (CHANNEL_DATA, {})})

        assert sorted(reader.list_steps(self.acquisition_file)) == ['phase_calibrated', 'preprocessed']

    def test_a_file_that_is_missing_has_no_step(self):
        reader = self.reader_holding({})

        assert reader.list_steps(self.acquisition_file) == []

    def test_a_step_is_read_back_with_its_array_and_scalar_metadata(self):
        reader = self.reader_holding({'preprocessed': (CHANNEL_DATA, {'grid_size': 2, 'x_step': 0.5})})

        stored = reader.read_step(self.acquisition_file, 'preprocessed')

        assert np.array_equal(stored.data, CHANNEL_DATA)
        assert (stored.metadata['grid_size'], stored.metadata['x_step']) == (2, 0.5)

    def test_a_step_never_stored_is_refused(self):
        reader = self.reader_holding({'preprocessed': (CHANNEL_DATA, {})})

        with pytest.raises(KeyError):
            reader.read_step(self.acquisition_file, 'interpolated')

    def test_a_step_of_a_missing_file_is_refused(self):
        reader = self.reader_holding({})

        with pytest.raises(FileNotFoundError):
            reader.read_step(self.acquisition_file, 'preprocessed')
