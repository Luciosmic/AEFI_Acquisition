"""
Measured Object Registry Panel — see, add, rename and delete the measured objects
the acquisition panels offer (see measured_object_registry_panel_intention.md).
"""

from typing import Callable, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QInputDialog, QLabel, QListWidget, QListWidgetItem, QMessageBox, QPushButton

from application.measured_object_registry.measured_object_service.dtos.measured_object_dto import MeasuredObjectDTO
from interface.widgets.panels.base_panel import BasePanel

_ERROR_STYLE = "color: #FF9800; font-weight: bold;"
_DONE_STYLE = "color: #4CAF50;"

# (title, label, current text) -> typed name, "" when cancelled
AskName = Callable[[str, str, str], str]
# name -> True when the deletion is confirmed
ConfirmDelete = Callable[[str], bool]


class MeasuredObjectRegistryPanel(BasePanel):
    register_requested = Signal(str)
    rename_requested = Signal(str, str)  # measured_object_id, new name
    delete_requested = Signal(str)  # measured_object_id

    def __init__(self, parent=None, ask_name: Optional[AskName] = None, confirm_delete: Optional[ConfirmDelete] = None):
        super().__init__("Objets mesurés", "#795548", parent)
        self._ask_name = ask_name or self._ask_name_dialog
        self._confirm_delete = confirm_delete or self._confirm_delete_dialog

        self.layout.addWidget(QLabel(
            "Objets proposés au démarrage d'une acquisition (Scan, Continuous Reading, Frequency Sweep)."
        ))
        self.list_widget = QListWidget()
        self.list_widget.itemSelectionChanged.connect(self._update_buttons)
        self.list_widget.itemDoubleClicked.connect(lambda _item: self._on_rename_clicked())
        self.layout.addWidget(self.list_widget, 1)

        buttons = QHBoxLayout()
        self.add_button = QPushButton("Nouvel objet…")
        self.rename_button = QPushButton("Renommer…")
        self.delete_button = QPushButton("Supprimer…")
        for button in (self.add_button, self.rename_button, self.delete_button):
            buttons.addWidget(button)
        self.add_button.clicked.connect(self._on_add_clicked)
        self.rename_button.clicked.connect(self._on_rename_clicked)
        self.delete_button.clicked.connect(self._on_delete_clicked)
        self.layout.addLayout(buttons)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.layout.addWidget(self.status_label)
        self._update_buttons()

    # -- from the presenter ------------------------------------------------------

    def set_measured_objects(self, measured_objects: List[MeasuredObjectDTO]) -> None:
        """Known measured_objects, sorted by name; the selection is kept when it still exists."""
        selected = self.selected_measured_object()
        self.list_widget.clear()
        for measured_object in measured_objects:
            item = QListWidgetItem(measured_object.name)
            item.setData(Qt.ItemDataRole.UserRole, measured_object)
            self.list_widget.addItem(item)
            if selected is not None and measured_object.measured_object_id == selected.measured_object_id:
                item.setSelected(True)
                self.list_widget.setCurrentItem(item)
        self._update_buttons()

    def on_measured_object_registered(self, measured_object: MeasuredObjectDTO, already_registered: bool) -> None:
        self.show_done(f"Déjà enregistré : {measured_object.name}" if already_registered else f"Enregistré : {measured_object.name}")

    def show_done(self, message: str) -> None:
        self.status_label.setStyleSheet(_DONE_STYLE)
        self.status_label.setText(message)

    def show_failure(self, reason: str) -> None:
        self.status_label.setStyleSheet(_ERROR_STYLE)
        self.status_label.setText(reason)

    # -- state -------------------------------------------------------------------

    def selected_measured_object(self) -> Optional[MeasuredObjectDTO]:
        items = self.list_widget.selectedItems()
        return items[0].data(Qt.ItemDataRole.UserRole) if items else None

    def _update_buttons(self) -> None:
        has_selection = self.selected_measured_object() is not None
        self.rename_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    # -- operator gestures -------------------------------------------------------

    def _on_add_clicked(self) -> None:
        name = self._ask_name("Nouvel objet mesuré", "Nom de l'objet mesuré :", "")
        if name and name.strip():
            self.register_requested.emit(name)

    def _on_rename_clicked(self) -> None:
        selected = self.selected_measured_object()
        if selected is None:
            return
        name = self._ask_name("Renommer l'objet mesuré", "Nouveau nom :", selected.name)
        if name and name.strip():
            self.rename_requested.emit(selected.measured_object_id, name)

    def _on_delete_clicked(self) -> None:
        selected = self.selected_measured_object()
        if selected is not None and self._confirm_delete(selected.name):
            self.delete_requested.emit(selected.measured_object_id)

    # -- default dialogs ---------------------------------------------------------

    def _ask_name_dialog(self, title: str, label: str, text: str) -> str:
        name, accepted = QInputDialog.getText(self, title, label, text=text)
        return name if accepted else ""

    def _confirm_delete_dialog(self, name: str) -> bool:
        answer = QMessageBox.question(
            self, "Supprimer l'objet mesuré",
            f"Supprimer « {name} » du registre ?\n\n"
            "Il ne sera plus proposé au démarrage d'une acquisition. "
            "Les exports déjà écrits gardent son nom et son identité.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes
