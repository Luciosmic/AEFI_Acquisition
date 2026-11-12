import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QValidator
from PySide6.QtWidgets import QApplication

from interface.widgets.lift_off_input.lift_off_input import LiftOffInput


def _input() -> LiftOffInput:
    QApplication.instance() or QApplication([])
    return LiftOffInput()


def test_empty_is_not_entered_never_zero():
    assert _input().lift_off_mm() is None


def test_decimal_point_or_comma_give_the_same_millimetres():
    field = _input()
    field.setText("8,5")
    assert field.lift_off_mm() == 8.5
    field.setText("8.5")
    assert field.lift_off_mm() == 8.5


def test_negative_or_text_is_refused_by_the_field():
    field = _input()  # kept alive: the validator belongs to it
    validator = field.validator()
    for text in ("-1", "abc", "8 mm"):
        assert validator.validate(text, 0)[0] == QValidator.Invalid, text


def test_hovering_gives_the_explicit_name():
    assert "distance_between_lowest_point_of_sphere_and_highest_point_of_object_under_test" in _input().toolTip()
