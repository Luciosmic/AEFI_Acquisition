"""
Operator Selector — choose the operator of an acquisition among the known
ones, or register a new one (see operator_selector_intention.md).
"""

from typing import Callable, List, Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QInputDialog, QToolTip

from application.services.operator_service.dtos.operator_dto import OperatorDTO

NO_OPERATOR_LABEL = "— opérateur —"
NEW_OPERATOR_LABEL = "Nouvel opérateur…"
_NEW_OPERATOR = "__new__"


class OperatorSelector(QComboBox):
    register_requested = Signal(str)

    def __init__(self, parent=None, ask_name: Optional[Callable[[], str]] = None):
        super().__init__(parent)
        self._ask_name = ask_name or self._ask_name_dialog
        self._operators: List[OperatorDTO] = []
        self._selected_id: Optional[str] = None
        self._pending = False
        self.setToolTip("Opérateur de l'acquisition — écrit dans acquisition-parameters.json (provenance.operator)")
        self.set_operators([])
        self.activated.connect(self._on_activated)

    def current_operator(self) -> Optional[OperatorDTO]:
        return next((o for o in self._operators if o.operator_id == self._selected_id), None)

    def set_operators(self, operators: List[OperatorDTO]) -> None:
        """Known operators (from the presenter); the current selection is kept."""
        self._operators = list(operators)
        self.blockSignals(True)
        self.clear()
        self.addItem(NO_OPERATOR_LABEL, None)
        for operator in self._operators:
            self.addItem(operator.name, operator.operator_id)
        self.addItem(NEW_OPERATOR_LABEL, _NEW_OPERATOR)
        self._show_selection()
        self.blockSignals(False)

    def on_operator_registered(self, operator: OperatorDTO, already_registered: bool) -> None:
        if not self._pending:
            return
        self._pending = False
        if all(o.operator_id != operator.operator_id for o in self._operators):
            self.set_operators(self._operators + [operator])
        self._selected_id = operator.operator_id
        self._show_selection()
        if already_registered:
            self._tell(f"Déjà enregistré : {operator.name}")

    def on_registration_failed(self, reason: str) -> None:
        if not self._pending:
            return
        self._pending = False
        self._show_selection()
        self._tell(f"Opérateur non enregistré : {reason}")

    def _on_activated(self, index: int) -> None:
        data = self.itemData(index)
        if data != _NEW_OPERATOR:
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
        name, accepted = QInputDialog.getText(self, "Nouvel opérateur", "Nom de l'opérateur :")
        return name if accepted else ""

    def _tell(self, message: str) -> None:
        self.setStatusTip(message)
        QToolTip.showText(self.mapToGlobal(self.rect().bottomLeft()), message, self)
