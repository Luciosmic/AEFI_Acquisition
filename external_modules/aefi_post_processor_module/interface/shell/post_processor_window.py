"""
PostProcessorWindow - The window of panels with its taskbar (see post_processor_window_intention.md).
"""

import logging
import os
from typing import NamedTuple, Sequence

from PySide6.QtWidgets import QVBoxLayout, QWidget

from ...aefi_acquisition_upstream.upstream_objects import (
    CarrierPresentationModel,
    ModernTaskbar,
    TaskbarPresentationModel,
    TaskbarPresenter,
    WindowsCarrier,
)

logger = logging.getLogger(__name__)

_TASKBAR_HEIGHT = 60


class PanelSpec(NamedTuple):
    """One panel of the window: its id, the title of its dock, its taskbar group and its widget."""

    panel_id: str
    title: str
    group: str
    widget: QWidget


class PostProcessorWindow(QWidget):
    def __init__(self, panels: Sequence[PanelSpec], layout_file: str):
        super().__init__()
        self._layout_file = layout_file
        self._panel_ids = [spec.panel_id for spec in panels]
        self._shown_once = False
        self.setWindowTitle("AEFI Post-Processor")
        self.resize(1400, 850)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.carrier_model = CarrierPresentationModel()
        self.carrier_view = WindowsCarrier()
        main_layout.addWidget(self.carrier_view, 1)
        self.carrier_view.panel_visibility_changed.connect(self._on_panel_visibility_changed)

        self.taskbar_model = TaskbarPresentationModel()
        self.taskbar_view = ModernTaskbar()
        self.taskbar_presenter = TaskbarPresenter(self.taskbar_model, self.taskbar_view)
        self.taskbar_view.setFixedHeight(_TASKBAR_HEIGHT)
        main_layout.addWidget(self.taskbar_view)
        self.taskbar_presenter.panel_toggle_requested.connect(self._on_panel_toggle_requested)

        for spec in panels:
            self.taskbar_presenter.register_panel(spec.panel_id, spec.title, group=spec.group)
            self.carrier_view.register_panel(spec.panel_id, spec.widget, spec.title)

        if not self._restore_layout():
            self.carrier_view.arrange_default_layout()

    def showEvent(self, event):
        super().showEvent(event)
        if self._shown_once:
            return
        self._shown_once = True
        for panel_id in self._panel_ids:
            dock = self.carrier_view._panels.get(panel_id)
            if dock is not None:
                self.taskbar_presenter.set_panel_visibility(panel_id, dock.isVisible())
        logger.info("window.shown panels=%s layout_file=%s", self._panel_ids, self._layout_file)

    def closeEvent(self, event):
        self._save_layout()
        event.accept()

    def _on_panel_toggle_requested(self, panel_id: str) -> None:
        dock = self.carrier_view._panels.get(panel_id)
        if dock is not None:
            dock.toggleView(not dock.isVisible())

    def _on_panel_visibility_changed(self, panel_id: str, visible: bool) -> None:
        self.taskbar_presenter.set_panel_visibility(panel_id, visible)

    def _save_layout(self) -> bool:
        try:
            state = self.carrier_view.save_layout()
            os.makedirs(os.path.dirname(self._layout_file) or ".", exist_ok=True)
            with open(self._layout_file, "wb") as f:
                f.write(bytes(state))
            return True
        except Exception as error:
            logger.warning("window.layout_not_saved file=%s error_type=%s error=%s", self._layout_file, type(error).__name__, error)
            return False

    def _restore_layout(self) -> bool:
        if not os.path.exists(self._layout_file):
            return False
        try:
            with open(self._layout_file, "rb") as f:
                self.carrier_view.restore_layout(f.read())
            return True
        except Exception as error:
            logger.warning("window.layout_not_restored file=%s error_type=%s error=%s", self._layout_file, type(error).__name__, error)
            return False
