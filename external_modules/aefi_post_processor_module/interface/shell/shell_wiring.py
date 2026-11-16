"""
shell_wiring - Builds the window of panels with its presenters and the services they call (see shell_wiring_intention.md).
"""

import logging
from typing import Tuple

from ..logs_panel.logs_panel import LogsPanel
from ..logs_presenter.logs_presenter import LogsPresenter
from .post_processor_window import PanelSpec, PostProcessorWindow

logger = logging.getLogger(__name__)


def build_window(feedback, log_file: str, layout_file: str) -> Tuple[PostProcessorWindow, LogsPresenter]:
    """The window with its panels, and the presenters that must stay alive as long as it does."""
    logs_panel = LogsPanel()
    logs_presenter = LogsPresenter(logs_panel, log_file)
    feedback.attach(logs_presenter.append_feedback)
    window = PostProcessorWindow(
        [PanelSpec("logs", "Logs", "Système", logs_panel)],
        layout_file,
    )
    return window, logs_presenter
