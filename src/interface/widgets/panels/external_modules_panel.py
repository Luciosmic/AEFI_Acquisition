"""Lance les applications sous external_modules/ depuis le dashboard."""
from __future__ import annotations

import os
import sys
from functools import partial

from PySide6.QtCore import QProcess
from PySide6.QtWidgets import QLabel, QMessageBox, QPushButton, QWidget, QVBoxLayout

from interface.widgets.panels.base_panel import BasePanel

_BTN_STYLE = """
QPushButton {{
    background-color: {bg};
    color: white;
    padding: 10px;
    border-radius: 5px;
    font-weight: bold;
}}
QPushButton:hover {{ background-color: {hover}; }}
QPushButton:disabled {{ background-color: #78909C; color: #CFD8DC; }}
"""


class ExternalModulesPanel(BasePanel):
    """Hub pour lancer les exécutables Python du dossier external_modules/."""

    _LAUNCHERS = (
        (
            "post",
            "Post-processing && visualisation",
            ("external_modules", "post_processor_module", "composition_root.py"),
            "#1976D2",
            "#1565C0",
        ),
        (
            "cube",
            "Visualiseur 3D (cube senseur)",
            ("external_modules", "cube_visualizer", "main.py"),
            "#00897B",
            "#00796B",
        ),
    )

    def __init__(self, parent=None):
        super().__init__("External Modules", "#8E24AA", parent)

        self._processes: dict[str, QProcess | None] = {k: None for k, *_ in self._LAUNCHERS}
        self._buttons: dict[str, QPushButton] = {}
        self._status_labels: dict[str, QLabel] = {}

        intro = QLabel(
            "Outils hors cœur applicatif (src/). Même interpréteur Python que cette application."
        )
        intro.setWordWrap(True)
        self.layout.addWidget(intro)

        for key, label, script_parts, bg, hover in self._LAUNCHERS:
            self.layout.addWidget(self._build_row(key, label, script_parts, bg, hover))

        self.layout.addStretch()

    @staticmethod
    def _repo_root() -> str:
        # panels/ -> widgets/ -> interface/ -> src/ -> repo root
        return os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        )

    def _build_row(
        self,
        key: str,
        label: str,
        script_parts: tuple[str, ...],
        bg: str,
        hover: str,
    ) -> QWidget:
        row = QWidget()
        v = QVBoxLayout(row)
        v.setContentsMargins(0, 8, 0, 0)

        btn = QPushButton(label)
        btn.setStyleSheet(_BTN_STYLE.format(bg=bg, hover=hover))
        btn.clicked.connect(partial(self._launch, key, script_parts, label))
        self._buttons[key] = btn
        v.addWidget(btn)

        st = QLabel("Prêt")
        st.setStyleSheet("color: #AAA; font-style: italic;")
        self._status_labels[key] = st
        v.addWidget(st)
        return row

    def _launch(
        self,
        key: str,
        script_parts: tuple[str, ...],
        button_label: str,
    ) -> None:
        proc = self._processes.get(key)
        if proc is not None and proc.state() == QProcess.Running:
            QMessageBox.information(
                self,
                "Déjà en cours",
                f"« {button_label} » est déjà lancé.",
            )
            return

        root = self._repo_root()
        script_path = os.path.join(root, *script_parts)
        python_exe = sys.executable

        print(f"[ExternalModulesPanel] {key}: {python_exe} {script_path}")

        process = QProcess(self)
        process.finished.connect(partial(self._on_finished, key, button_label))
        process.errorOccurred.connect(partial(self._on_error, key, button_label))

        self._processes[key] = process
        btn = self._buttons[key]
        btn.setText(f"{button_label} — en cours…")
        btn.setEnabled(False)
        self._status_labels[key].setText("Exécution…")
        self._status_labels[key].setStyleSheet("color: #4CAF50; font-weight: bold;")

        process.start(python_exe, [script_path])

    def _on_finished(self, key: str, default_button_text: str, exit_code: int, _exit_status) -> None:
        print(f"[ExternalModulesPanel] {key} finished code={exit_code}")
        self._status_labels[key].setText(f"Terminé (code {exit_code})")
        self._status_labels[key].setStyleSheet("color: #AAA;")
        self._buttons[key].setText(default_button_text)
        self._buttons[key].setEnabled(True)

    def _on_error(self, key: str, default_button_text: str, error) -> None:
        print(f"[ExternalModulesPanel] {key} error: {error}")
        self._status_labels[key].setText(f"Erreur ({error})")
        self._status_labels[key].setStyleSheet("color: #F44336;")
        self._buttons[key].setText(default_button_text)
        self._buttons[key].setEnabled(True)
