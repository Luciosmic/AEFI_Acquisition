"""
AcquisitionsPanel - Humble view of the acquisitions: shows the rows it is given and reports the clicks.
Its behaviour lives in acquisitions_presenter (see acquisitions_presenter_intention.md).
"""

from PySide6.QtCore import QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

_COLUMNS = ("Acquisition", "Type", "Objet", "État", "Détail")


class AcquisitionsPanel(QWidget):
    selection_changed = Signal(list)  # the folder names of the selected rows
    process_selection_requested = Signal()
    process_pending_requested = Signal()
    open_folder_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, len(_COLUMNS))
        self.table.setHorizontalHeaderLabels(list(_COLUMNS))
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self._report_selection)
        layout.addWidget(self.table)

        buttons = QHBoxLayout()
        for text, signal in (
            ("Traiter la sélection", self.process_selection_requested),
            ("Traiter ce qui est à recalculer", self.process_pending_requested),
            ("Ouvrir le dossier", self.open_folder_requested),
        ):
            button = QPushButton(text)
            button.clicked.connect(signal.emit)
            buttons.addWidget(button)
        buttons.addStretch()
        layout.addLayout(buttons)

    def set_rows(self, rows) -> None:
        self.table.blockSignals(True)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, text in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(text))
        self.table.blockSignals(False)

    def open_folder(self, path: str) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def _report_selection(self) -> None:
        rows = sorted({index.row() for index in self.table.selectedIndexes()})
        self.selection_changed.emit([self.table.item(r, 0).text() for r in rows])
