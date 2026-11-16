"""Suite de contrat du port ICsvScanReader : passée par l'adaptateur réel et par son Fake."""

import re

import numpy as np
import pytest

from ....application.post_processing_service.dtos.scan_samples_dto import ScanSamplesDTO

X = np.array([0.0, 1.0, 0.0, 1.0])
Y = np.array([0.0, 0.0, 1.0, 1.0])
VALUES = np.array([[1.0, 0.5, -1.0, 0.0], [2.0, 0.25, -2.0, 1.0], [3.0, 0.125, -3.0, 2.0], [4.0, 0.0, -4.0, 3.0]])
CHANNELS = ('voltage_x_in_phase', 'voltage_x_quadrature', 'voltage_z_in_phase', 'voltage_z_quadrature')


class CsvScanReaderContract:
    """Hérité par une classe de test qui fournit `reader_holding(name, samples)` : un lecteur dont le fichier `name` contient `samples`."""

    def reader_holding(self, name: str, samples: ScanSamplesDTO):
        raise NotImplementedError

    def reader_without_files(self):
        raise NotImplementedError

    def test_reading_gives_back_the_points_and_their_channels(self):
        samples = ScanSamplesDTO(x=X, y=Y, values=VALUES, channel_names=CHANNELS)

        read = self.reader_holding("scan.csv", samples).read(self.path_of("scan.csv"))

        assert np.array_equal(read.x, X) and np.array_equal(read.y, Y)
        assert np.array_equal(read.values, VALUES)
        assert tuple(read.channel_names) == CHANNELS

    def test_a_file_without_voltage_columns_has_no_channel(self):
        samples = ScanSamplesDTO(x=X, y=Y, values=np.empty((4, 0)), channel_names=())

        read = self.reader_holding("empty.csv", samples).read(self.path_of("empty.csv"))

        assert tuple(read.channel_names) == () and read.values.shape == (4, 0)

    def test_a_missing_file_is_refused_with_its_path(self):
        reader = self.reader_without_files()
        missing = self.path_of("absent.csv")

        with pytest.raises(FileNotFoundError, match="CSV file not found: " + re.escape(missing)):
            reader.read(missing)
