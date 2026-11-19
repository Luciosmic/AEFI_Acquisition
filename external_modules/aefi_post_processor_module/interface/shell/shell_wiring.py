"""
shell_wiring - Builds the window of panels with its presenters and the services they call (see shell_wiring_intention.md).
"""

import logging
from typing import Callable, NamedTuple

from ..acquisition_parameters_panel.acquisition_parameters_panel import AcquisitionParametersPanel
from ..acquisition_parameters_presenter.acquisition_parameters_presenter import AcquisitionParametersPresenter
from ..acquisitions_panel.acquisitions_panel import AcquisitionsPanel
from ..acquisitions_presenter.acquisitions_presenter import AcquisitionsPresenter
from ..field_map_panel.field_map_panel import FieldMapPanel
from ..field_map_presenter.field_map_presenter import FieldMapPresenter
from ..figure_factory.figure_factory import FigureFactory
from ..logs_panel.logs_panel import LogsPanel
from ..logs_presenter.logs_presenter import LogsPresenter
from .headless_wiring import build_acquisition_catalog_service, build_field_map_service, build_post_processing_service
from .post_processor_window import PanelSpec, PostProcessorWindow

logger = logging.getLogger(__name__)


class Shell(NamedTuple):
    """The window and the presenters that must stay alive as long as it does."""

    window: PostProcessorWindow
    acquisitions_presenter: AcquisitionsPresenter
    acquisition_parameters_presenter: AcquisitionParametersPresenter
    field_map_presenter: FieldMapPresenter
    logs_presenter: LogsPresenter


def build_shell(
    feedback,
    log_file: str,
    layout_file: str,
    export_folder: str,
    parameters_provider: Callable[[], object],
    rotation_origin: str,
) -> Shell:
    logs_panel = LogsPanel()
    logs_presenter = LogsPresenter(logs_panel, log_file)
    feedback.attach(logs_presenter.append_feedback)

    field_map_panel = FieldMapPanel()
    field_map_presenter = FieldMapPresenter(field_map_panel, build_field_map_service(), FigureFactory())

    acquisitions_panel = AcquisitionsPanel()
    acquisitions_presenter = AcquisitionsPresenter(
        acquisitions_panel, build_acquisition_catalog_service(), build_post_processing_service,
        parameters_provider, export_folder, rotation_origin,
    )
    acquisitions_presenter.when_acquisition_chosen(field_map_presenter.show_acquisition)

    parameters_panel = AcquisitionParametersPanel()
    parameters_presenter = AcquisitionParametersPresenter(parameters_panel)
    parameters_presenter.clear()
    acquisitions_presenter.when_status_chosen(parameters_presenter.show, parameters_presenter.clear)
    acquisitions_presenter.when_processed(field_map_presenter.refresh)

    window = PostProcessorWindow(
        [
            PanelSpec("acquisitions", "Acquisitions", "Données", acquisitions_panel),
            PanelSpec("acquisition_parameters", "Paramètres d'acquisition", "Données", parameters_panel),
            PanelSpec("field_map", "Carte", "Visualisation", field_map_panel),
            PanelSpec("logs", "Logs", "Système", logs_panel),
        ],
        layout_file,
    )
    return Shell(window, acquisitions_presenter, parameters_presenter, field_map_presenter, logs_presenter)
