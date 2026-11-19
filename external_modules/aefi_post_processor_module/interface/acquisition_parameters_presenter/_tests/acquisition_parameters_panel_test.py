"""La vue humble du panneau « Paramètres d'acquisition » : elle montre ce que le presenter lui donne, rien d'autre."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton

from ...acquisition_parameters_panel.acquisition_parameters_panel import AcquisitionParametersPanel


def _texts(panel):
    return [label.text() for label in panel.findChildren(QLabel)]


def test_the_panel_shows_the_title_and_every_label_with_its_value(qtbot):
    panel = AcquisitionParametersPanel()
    qtbot.addWidget(panel)

    panel.set_title("2026-11-13_103000_stepScan_bouteille")
    panel.set_rows([("Objet mesuré", "bouteille_cristalline"), ("Angle θx appliqué", "34.9 °")])

    texts = _texts(panel)
    assert "2026-11-13_103000_stepScan_bouteille" in texts
    assert "Objet mesuré" in texts and "bouteille_cristalline" in texts
    assert "Angle θx appliqué" in texts and "34.9 °" in texts


def test_new_rows_replace_the_previous_ones(qtbot):
    panel = AcquisitionParametersPanel()
    qtbot.addWidget(panel)
    panel.set_rows([("Objet mesuré", "a")])

    panel.set_rows([("Version du schéma", "1.4")])

    texts = _texts(panel)
    assert "Version du schéma" in texts and "Objet mesuré" not in texts


def test_the_panel_is_read_only_it_has_no_button_and_no_editable_field(qtbot):
    panel = AcquisitionParametersPanel()
    qtbot.addWidget(panel)
    panel.set_rows([("Objet mesuré", "a")])

    assert panel.findChildren(QPushButton) == []
    for label in panel.findChildren(QLabel):
        assert not (label.textInteractionFlags() & Qt.TextInteractionFlag.TextEditable)
