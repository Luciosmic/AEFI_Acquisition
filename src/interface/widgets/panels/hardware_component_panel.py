"""
Hardware Component Panel

One calibration tab per hardware component kind, built from the kind's
quantity list: pick the mounted component from the catalog, and record /
complete a component's characterization (every quantity may be left
"non caractérisée").
"""

from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

_MUTED = "color: #888; font-style: italic;"
_DEBT = "color: #d98c00; font-weight: bold;"
_ERROR = "color: #c62828;"


def _format(value: Any) -> str:
    if isinstance(value, tuple):
        return "; ".join(f"{x:g}:{y:g}" for x, y in value)
    return f"{value:g}"


def _parse_curve(text: str) -> Tuple[Tuple[float, float], ...]:
    points = []
    for chunk in text.replace(",", ";").split(";"):
        if chunk.strip():
            x, y = chunk.split(":")
            points.append((float(x), float(y)))
    return tuple(points)


class HardwareComponentPanel(QWidget):
    """Catalog + mounted component + characterization form for one kind."""

    # component name, {quantity key: float | ((x, y), ...) | None}  (None = not characterized)
    save_requested = Signal(str, object)
    mount_requested = Signal(str)

    def __init__(self, kind, parent=None):
        """`kind`: HardwareComponentKindDTO (key, label, quantities)."""
        super().__init__(parent)
        self._kind = kind
        self._components: Dict[str, object] = {}
        self._fields: Dict[str, Tuple[QLineEdit, QCheckBox]] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # -- mounted component ----------------------------------------------------
        grp_mounted = QGroupBox("Monté sur le banc")
        l_mounted = QFormLayout(grp_mounted)
        self.lbl_mounted = QLabel()
        self.lbl_mounted.setWordWrap(True)
        l_mounted.addRow(self.lbl_mounted)
        self.combo_components = QComboBox()
        self.combo_components.currentTextChanged.connect(self._load_component_into_form)
        l_mounted.addRow("Caractérisés :", self.combo_components)
        self.btn_mount = QPushButton("Monter le composant sélectionné")
        self.btn_mount.clicked.connect(self._on_mount_clicked)
        l_mounted.addRow(self.btn_mount)
        if kind.key.endswith("_board"):
            lbl_restart = QLabel("Changer de carte : redémarrer ensuite l'application pour l'appliquer aux autres calibrations.")
            lbl_restart.setWordWrap(True)
            lbl_restart.setStyleSheet(_MUTED)
            l_mounted.addRow(lbl_restart)
        layout.addWidget(grp_mounted)

        # -- characterization -----------------------------------------------------
        grp_values = QGroupBox("Caractérisation (nouveau composant, ou compléter un composant existant)")
        l_values = QFormLayout(grp_values)
        self.edit_name = QLineEdit()
        self.edit_name.setPlaceholderText("nom unique, obligatoire")
        l_values.addRow("Nom :", self.edit_name)
        for quantity in kind.quantities:
            edit = QLineEdit()
            if quantity.curve_x_label:
                edit.setPlaceholderText(f"{quantity.curve_x_label}:valeur ; ex. 1:1000; 8:700")
            else:
                edit.setPlaceholderText("ex. 9.8 ou 2.9e-7")
            unknown = QCheckBox("non caractérisée")
            unknown.toggled.connect(edit.setDisabled)
            unknown.setChecked(True)
            row = QHBoxLayout()
            row.addWidget(edit, 1)
            row.addWidget(unknown)
            curve_suffix = f" vs {quantity.curve_x_label}" if quantity.curve_x_label else ""
            l_values.addRow(f"{quantity.label}{curve_suffix} [{quantity.unit}] :", row)
            self._fields[quantity.key] = (edit, unknown)
        self.btn_save = QPushButton("Enregistrer la caractérisation")
        self.btn_save.clicked.connect(self._on_save_clicked)
        l_values.addRow(self.btn_save)
        self.lbl_error = QLabel()
        self.lbl_error.setWordWrap(True)
        self.lbl_error.setStyleSheet(_ERROR)
        l_values.addRow(self.lbl_error)
        layout.addWidget(grp_values)

        layout.addStretch()
        self.on_mounted_component_updated(None)
        self.btn_mount.setEnabled(False)

    # -- user actions -------------------------------------------------------------

    def _on_save_clicked(self):
        values: Dict[str, Any] = {}
        for quantity in self._kind.quantities:
            edit, unknown = self._fields[quantity.key]
            if unknown.isChecked():
                values[quantity.key] = None
                continue
            try:
                values[quantity.key] = _parse_curve(edit.text()) if quantity.curve_x_label else float(edit.text())
            except ValueError:
                self.set_status_message(
                    f"Erreur: {quantity.label} : valeur illisible « {edit.text()} » (ou cocher « non caractérisée »)"
                )
                return
        self.lbl_error.clear()
        self.save_requested.emit(self.edit_name.text().strip(), values)

    def set_status_message(self, message: str) -> None:
        """Presenter feedback (success or "Erreur: ..." refused by the domain)."""
        self.lbl_error.setStyleSheet(_ERROR if message.startswith("Erreur") else _MUTED)
        self.lbl_error.setText(message)

    def _on_mount_clicked(self):
        if self.combo_components.currentText():
            self.mount_requested.emit(self.combo_components.currentText())

    def _load_component_into_form(self, name: str) -> None:
        dto = self._components.get(name)
        if dto is None:
            return
        self.edit_name.setText(dto.component_name)
        for key, (edit, unknown) in self._fields.items():
            value = dto.values.get(key)
            unknown.setChecked(value is None)
            edit.setText("" if value is None else _format(value))

    # -- presenter slots ----------------------------------------------------------

    def on_components_listed(self, components: List[object]) -> None:
        current = self.combo_components.currentText()
        self._components = {dto.component_name: dto for dto in components}
        self.combo_components.blockSignals(True)
        self.combo_components.clear()
        self.combo_components.addItems(list(self._components))
        if current in self._components:
            self.combo_components.setCurrentText(current)
        self.combo_components.blockSignals(False)
        self.btn_mount.setEnabled(bool(self._components))

    def on_mounted_component_updated(self, dto: Optional[object]) -> None:
        if dto is None:
            self.lbl_mounted.setText("RIEN DE MONTÉ — configuration incomplète. Caractériser un composant puis le monter.")
            self.lbl_mounted.setStyleSheet(_DEBT)
            return
        parts = []
        for quantity in self._kind.quantities:
            value = dto.values.get(quantity.key)
            shown = "NON CARACTÉRISÉE" if value is None else f"{_format(value)} {quantity.unit}"
            parts.append(f"{quantity.label} = {shown}")
        self.lbl_mounted.setText(
            f"{dto.component_name} — " + " ; ".join(parts)
            + f" — caractérisé le {dto.recorded_at.strftime('%Y-%m-%d %H:%M')}"
        )
        self.lbl_mounted.setStyleSheet(_DEBT if dto.uncharacterized else _MUTED)
        self.combo_components.setCurrentText(dto.component_name)
        self._load_component_into_form(dto.component_name)
