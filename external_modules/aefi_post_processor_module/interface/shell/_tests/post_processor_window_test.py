"""La fenêtre à panneaux sous Qt hors écran : panneaux dans la barre de tâches, disposition dans son propre fichier."""

import logging
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QLabel

from ..post_processor_window import PanelSpec, PostProcessorWindow


def _window(layout_file):
    return PostProcessorWindow(
        [PanelSpec("one", "Un", "Données", QLabel("un")), PanelSpec("two", "Deux", "Système", QLabel("deux"))],
        str(layout_file),
    )


def test_the_window_lists_its_panels_in_the_taskbar_and_says_it_is_shown_once(qtbot, tmp_path, caplog):
    window = _window(tmp_path / "layout.dat")
    qtbot.addWidget(window)

    with caplog.at_level(logging.INFO):
        window.show()
        window.hide()
        window.show()

    assert [panel.id for panel in window.taskbar_model.panels] == ["one", "two"]
    shown = [r.getMessage() for r in caplog.records if r.getMessage().startswith("window.shown")]
    assert len(shown) == 1 and "['one', 'two']" in shown[0]


def test_the_layout_is_saved_in_the_file_it_was_given_and_restored_by_the_next_window(qtbot, tmp_path):
    layout_file = tmp_path / "state" / "post_processor_layout.dat"
    first = _window(layout_file)
    qtbot.addWidget(first)
    first.show()

    first.close()

    assert layout_file.exists() and layout_file.stat().st_size > 0
    second = _window(layout_file)
    qtbot.addWidget(second)
    second.show()
    assert set(second.carrier_view._panels) == {"one", "two"}


def test_an_unreadable_layout_file_does_not_stop_the_window(qtbot, tmp_path):
    layout_file = tmp_path / "layout.dat"
    layout_file.write_bytes(b"not a layout")

    window = _window(layout_file)
    qtbot.addWidget(window)

    assert set(window.carrier_view._panels) == {"one", "two"}
