from PySide6.QtWidgets import QApplication, QWidget

from interface.widgets.layouts.flow_layout import FlowLayout

app = QApplication.instance() or QApplication([])


def _strip(n_items: int, item_width: int = 100) -> QWidget:
    """Returns the host widget — it owns the layout, so it must outlive the asserts."""
    host = QWidget()
    layout = FlowLayout(host, spacing=0)
    for _ in range(n_items):
        w = QWidget()
        w.setFixedSize(item_width, 20)
        layout.addWidget(w)
    return host


def test_minimum_width_is_the_widest_item_not_the_sum():
    host = _strip(5)
    assert host.layout().minimumSize().width() == 100


def test_items_wrap_onto_more_rows_when_narrow():
    host = _strip(4)
    layout = host.layout()
    assert layout.heightForWidth(400) == 20  # one row
    assert layout.heightForWidth(200) == 40  # two rows
    assert layout.heightForWidth(100) == 80  # one item per row
