"""
AcquisitionsPanel - Humble view of the acquisitions: shows the rows it is given and reports the clicks.
Its behaviour lives in acquisitions_presenter (see acquisitions_presenter_intention.md).
"""

from PySide6.QtCore import Qt, QUrl, Signal
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

_COLUMNS = ("Dossier", "Date", "Type", "Objet mesuré", "Lift-off", "État", "Détail")
_NAME = Qt.ItemDataRole.UserRole  # the acquisition folder name, carried by the first cell of a row


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
            name, *shown = row
            for c, text in enumerate(shown):
                item = QTableWidgetItem(text)
                item.setToolTip(name)
                self.table.setItem(r, c, item)
            self.table.item(r, 0).setData(_NAME, name)
        self.table.blockSignals(False)

    def open_folder(self, path: str) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def _report_selection(self) -> None:
        rows = sorted({index.row() for index in self.table.selectedIndexes()})
        self.selection_changed.emit([self.table.item(r, 0).data(_NAME) for r in rows])
