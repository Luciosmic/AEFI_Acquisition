"""Lift-off input: the sphere-to-object distance in mm (see lift_off_input_intention.md)."""

from typing import Optional

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import QLineEdit

LIFT_OFF_LABEL = "Lift-off (mm):"
LIFT_OFF_TOOLTIP = (
    "Lift-off = distance_between_lowest_point_of_sphere_and_highest_point_of_object_under_test\n"
    "Distance verticale entre le point le plus bas des sphères et le point le plus haut\n"
    "de l'objet mesuré, en mm.\n"
    "Écrite dans acquisition-parameters.json (feature_of_interest) ; vide = non saisie, signalée."
)


class LiftOffInput(QLineEdit):
    """Positive distance in mm, decimal point or comma; empty = not entered."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("mm")
        self.setToolTip(LIFT_OFF_TOOLTIP)
        self.setValidator(QRegularExpressionValidator(QRegularExpression(r"^\d{0,4}([.,]\d{0,3})?$"), self))

    def lift_off_mm(self) -> Optional[float]:
        text = self.text().strip().replace(",", ".")
        if text in ("", "."):
            return None
        return float(text)
