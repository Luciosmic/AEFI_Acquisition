import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel

from interface.widgets.collapsible_section.collapsible_section import CollapsibleSection


def _section(expanded=False):
    QApplication.instance() or QApplication([])
    section = CollapsibleSection("Comment calibrer à la main", expanded=expanded)
    content = QLabel("étapes")
    section.set_content_widget(content)
    section.show()
    return section, content


def test_it_is_folded_by_default_and_the_title_stays_visible():
    section, content = _section()

    assert not section.is_expanded()
    assert not content.isVisible()
    assert section.header.text() == "Comment calibrer à la main"
    assert section.header.isVisible()


def test_clicking_the_title_unfolds_then_folds_the_content():
    section, content = _section()

    section.header.click()
    assert section.is_expanded() and content.isVisible()

    section.header.click()
    assert not section.is_expanded() and not content.isVisible()
