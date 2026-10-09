import dataclasses

import pytest

from domain.scan.value_objects.expected_source.expected_source import ExpectedSource


def test_required_by_default_and_frozen():
    source = ExpectedSource(3)
    assert source.count == 3 and source.required is True
    with pytest.raises(dataclasses.FrozenInstanceError):
        source.count = 1


def test_count_must_be_positive():
    with pytest.raises(ValueError):
        ExpectedSource(0)
