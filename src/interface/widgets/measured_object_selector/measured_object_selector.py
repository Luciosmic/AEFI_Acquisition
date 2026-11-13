"""
MeasuredObject Selector — choose the measured_object of an acquisition among the known
ones, or register a new one (see measured_object_selector_intention.md).
"""

from typing import Callable, List, Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QInputDialog, QToolTip

from application.measured_object_registry.measured_object_service.dtos.measured_object_dto import MeasuredObjectDTO

NO_MEASURED_OBJECT_LABEL = "— objet mesuré —"
NEW_MEASURED_OBJECT_LABEL = "Nouvel objet mesuré…"
_NEW_MEASURED_OBJECT = "__new__"


class MeasuredObjectSelector(QComboBox):
    register_requested = Signal(str)

    def __init__(self, parent=None, ask_name: Optional[Callable[[], str]] = None):
        super().__init__(parent)
        self._ask_name = ask_name or self._ask_name_dialog
        self._measured_objects: List[MeasuredObjectDTO] = []
        self._selected_id: Optional[str] = None
        self._pending = False
        self.setToolTip("Objet mesuré de l'acquisition — écrit dans acquisition-parameters.json (feature_of_interest)")
        self.set_measured_objects([])
        self.activated.connect(self._on_activated)

    def current_measured_object(self) -> Optional[MeasuredObjectDTO]:
        return next((o for o in self._measured_objects if o.measured_object_id == self._selected_id), None)

    def set_measured_objects(self, measured_objects: List[MeasuredObjectDTO]) -> None:
        """Known measured_objects (from the presenter); the current selection is kept."""
        self._measured_objects = list(measured_objects)
        self.blockSignals(True)
        self.clear()
        self.addItem(NO_MEASURED_OBJECT_LABEL, None)
        for measured_object in self._measured_objects:
            self.addItem(measured_object.name, measured_object.measured_object_id)
        self.addItem(NEW_MEASURED_OBJECT_LABEL, _NEW_MEASURED_OBJECT)
        self._show_selection()
        self.blockSignals(False)

    def on_measured_object_registered(self, measured_object: MeasuredObjectDTO, already_registered: bool) -> None:
        if not self._pending:
            return
        self._pending = False
        if all(o.measured_object_id != measured_object.measured_object_id for o in self._measured_objects):
            self.set_measured_objects(self._measured_objects + [measured_object])
        self._selected_id = measured_object.measured_object_id
        self._show_selection()
        if already_registered:
            self._tell(f"Déjà enregistré : {measured_object.name}")

    def on_registration_failed(self, reason: str) -> None:
        if not self._pending:
            return
        self._pending = False
        self._show_selection()
        self._tell(f"Objet mesuré non enregistré : {reason}")

    def _on_activated(self, index: int) -> None:
        data = self.itemData(index)
        if data != _NEW_MEASURED_OBJECT:
            self._selected_id = data
            return
        self._show_selection()  # back to the current choice while the name is typed
        name = self._ask_name()
        if name and name.strip():
            self._pending = True
            self.register_requested.emit(name)

    def _show_selection(self) -> None:
        index = self.findData(self._selected_id) if self._selected_id else 0
        self.setCurrentIndex(index if index >= 0 else 0)
        if index < 0:
            self._selected_id = None

    def _ask_name_dialog(self) -> str:
        name, accepted = QInputDialog.getText(self, "Nouvel objet mesuré", "Nom de l'objet mesuré :")
        return name if accepted else ""

    def _tell(self, message: str) -> None:
        self.setStatusTip(message)
        QToolTip.showText(self.mapToGlobal(self.rect().bottomLeft()), message, self)
