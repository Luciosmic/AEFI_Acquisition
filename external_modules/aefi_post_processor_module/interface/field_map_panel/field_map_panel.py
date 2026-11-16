"""
FieldMapPanel - Humble view of the map: shows the steps, the figure and the texts it is given and reports the clicks.
Its behaviour lives in field_map_presenter (see field_map_presenter_intention.md).
"""

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QListWidget, QVBoxLayout, QWidget


class FieldMapPanel(QWidget):
    step_selected = Signal(str)  # the text of the chosen item
    cursor_moved = Signal(object)  # the matplotlib motion event

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)

        side = QWidget()
        side.setFixedWidth(260)
        side_layout = QVBoxLayout(side)
        side_layout.addWidget(QLabel("Étape du traitement :"))
        self.steps = QListWidget()
        self.steps.currentTextChanged.connect(self.step_selected.emit)
        side_layout.addWidget(self.steps)
        self.rotation_label = QLabel("Rotation: N/A")
        self.reference_label = QLabel("Ref Point: N/A")
        self.cursor_label = QLabel("Cursor: Out of axes")
        self.cursor_label.setStyleSheet("color: #00FFFF; font-weight: bold; font-size: 10pt;")
        for label in (self.rotation_label, self.reference_label, self.cursor_label):
            side_layout.addWidget(label)
        layout.addWidget(side)

        self.plot_layout = QVBoxLayout()
        self.placeholder = QLabel("Choisissez une acquisition, puis une étape.")
        self.plot_layout.addWidget(self.placeholder)
        layout.addLayout(self.plot_layout, 1)

    def set_steps(self, steps) -> None:
        self.steps.clear()
        self.steps.addItems(steps)

    def select_step(self, display_name: str) -> None:
        self.steps.blockSignals(True)
        for row in range(self.steps.count()):
            if self.steps.item(row).text() == display_name:
                self.steps.setCurrentRow(row)
        self.steps.blockSignals(False)

    def clear_map(self) -> None:
        self._remove_plot_widgets()
        self.plot_layout.addWidget(self.placeholder)
        self.placeholder.show()

    def show_figure(self, figure) -> None:
        self._remove_plot_widgets()
        canvas = FigureCanvasQTAgg(figure)
        self.plot_layout.addWidget(canvas)
        canvas.mpl_connect('motion_notify_event', self.cursor_moved.emit)

    def set_frame_info(self, rotation: str, reference_point: str) -> None:
        self.rotation_label.setText(f"Rotation: {rotation}")
        self.reference_label.setText(f"Ref Point: {reference_point}")

    def set_cursor_text(self, text: str) -> None:
        self.cursor_label.setText(text)

    def _remove_plot_widgets(self) -> None:
        for i in reversed(range(self.plot_layout.count())):
            widget = self.plot_layout.itemAt(i).widget()
            if widget is not None:
                self.plot_layout.removeWidget(widget)
                if widget is self.placeholder:
                    widget.hide()
                else:
                    widget.deleteLater()
