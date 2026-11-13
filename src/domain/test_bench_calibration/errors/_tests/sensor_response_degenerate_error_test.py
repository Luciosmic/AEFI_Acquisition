"""Caractérisation de errors : le comportement actuel, sans le changer."""
import pytest

from domain.test_bench_calibration.errors.sensor_response_degenerate_error import SensorResponseDegenerateError
from domain.test_bench_calibration.errors.source_geometry_inconsistent_error import SourceGeometryInconsistentError


def test_sensorresponsedegenerateerror_est_une_exception_qui_garde_son_message():
    with pytest.raises(SensorResponseDegenerateError) as info:
        raise SensorResponseDegenerateError("raison")
    assert "raison" in str(info.value)


def test_sourcegeometryinconsistenterror_est_une_exception_qui_garde_son_message():
    with pytest.raises(SourceGeometryInconsistentError) as info:
        raise SourceGeometryInconsistentError("raison")
    assert "raison" in str(info.value)
