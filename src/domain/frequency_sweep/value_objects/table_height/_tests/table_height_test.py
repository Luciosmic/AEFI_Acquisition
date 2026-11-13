import math

import pytest

from domain.frequency_sweep.value_objects.table_height.table_height import TableHeight


def test_keeps_the_height_given_by_the_operator():
    assert TableHeight(123.5).millimetres == 123.5


@pytest.mark.parametrize("value", [math.nan, math.inf])
def test_refuses_a_height_that_is_not_a_number(value):
    with pytest.raises(ValueError):
        TableHeight(value)
