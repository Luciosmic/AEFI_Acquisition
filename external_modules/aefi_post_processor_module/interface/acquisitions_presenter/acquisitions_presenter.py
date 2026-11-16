"""
AcquisitionsPresenter - What the Acquisitions panel shows and does (see acquisitions_presenter_intention.md).
"""

import logging
import time
from typing import Callable, Dict, List, NamedTuple, Optional, Tuple

from ...application.acquisition_catalog_service.dtos.acquisition_outcome_dto import AcquisitionOutcomeDTO
from ...application.acquisition_catalog_service.dtos.acquisition_status_dto import (
    FAILED,
    PROCESSED,
    TO_RECOMPUTE,
    AcquisitionStatusDTO,
)
from ...application.acquisition_catalog_service.dtos.list_acquisitions_dto import ListAcquisitionsDTO
from ...application.post_processing_service.dtos.process_scan_dto import ProcessScanDTO

logger = logging.getLogger(__name__)

_KIND_LABELS = {"stepScan": "pas à pas", "flyScan": "à la volée"}
_STATE_LABELS = {PROCESSED: "traitée", TO_RECOMPUTE: "à recalculer", FAILED: "en échec"}
_REASON_LABELS = {
    "new": "jamais traitée",
    "incomplete": "fichier d'étapes sans première étape",
    "forced": "recalcul demandé",
    "source_newer": "scan modifié depuis le traitement",
}


class AcquisitionRow(NamedTuple):
    """One line of the panel, all text: the folder name (what the view reports back), type, object, state and detail."""

    name: str
    kind: str
    measured_object: str
    state: str
    detail: str


class _Batch(NamedTuple):
    processed: List[str]
    skipped: List[str]
    failed: Dict[str, str]  # acquisition -> the step that failed


def _measured_object(name: str) -> str:
    """The object named in `<timestamp>_<stepScan|flyScan>_<object>`, until the acquisition parameters are read (tranche 2)."""
    parts = name.split("_", 2)
    return parts[2] if len(parts) == 3 else name


class AcquisitionsPresenter:
    """
    `processor_factory(acquisition_file)` rends le service de traitement lié au fichier de cette acquisition et un objet
    qui se ferme ; `parameters_provider()` rend les paramètres du traitement, appelé à chaque acquisition traitée.
    """

    def __init__(
        self,
        view,
        catalog_service,
        processor_factory: Callable[[str], Tuple[object, object]],
        parameters_provider: Callable[[], object],
        export_folder: str,
        rotation_origin: str = "ideal_template",
    ):
        self._view = view
        self._catalog = catalog_service
        self._processor_factory = processor_factory
        self._parameters_provider = parameters_provider
        self._export_folder = export_folder
        self._rotation_origin = rotation_origin
        self._statuses: Dict[str, AcquisitionStatusDTO] = {}
        self._selected: List[str] = []
        self._chosen_listeners: List[Callable[[str, str], None]] = []
        self._processed_listeners: List[Callable[[], None]] = []
        view.selection_changed.connect(self.on_selection_changed)
        view.process_selection_requested.connect(self.process_selection)
        view.process_pending_requested.connect(self.process_pending)
        view.open_folder_requested.connect(self.on_open_folder_requested)

    def when_acquisition_chosen(self, listener: Callable[[str, str], None]) -> None:
        """`listener(name, acquisition_file)` is called each time the selection names an acquisition."""
        self._chosen_listeners.append(listener)

    def when_processed(self, listener: Callable[[], None]) -> None:
        """`listener()` is called after a batch, once the list shows the new states."""
        self._processed_listeners.append(listener)

    def refresh(self, force: bool = False) -> None:
        """List the acquisitions with their state. Computes nothing and writes no file."""
        statuses = self._catalog.list_acquisitions(ListAcquisitionsDTO(self._export_folder, force))
        self._statuses = {status.name: status for status in statuses}
        self._selected = [name for name in self._selected if name in self._statuses]
        self._view.set_rows([self._row(status) for status in statuses])
        if statuses:
            logger.info("acquisitions.shown export=%s count=%d", self._export_folder, len(statuses))
        else:
            logger.warning("acquisitions.none_found export=%s pattern=*_<stepScan|flyScan>_*/*_aefi.csv", self._export_folder)

    def on_selection_changed(self, names: List[str]) -> None:
        self._selected = [name for name in names if name in self._statuses]
        if self._selected:
            status = self._statuses[self._selected[0]]
            for listener in self._chosen_listeners:
                listener(status.name, status.acquisition_file)

    def process_pending(self, force: bool = False) -> None:
        """Process every acquisition to recompute (all of them when forced)."""
        statuses = self._catalog.list_acquisitions(ListAcquisitionsDTO(self._export_folder, force))
        self._statuses = {status.name: status for status in statuses}
        targets = [status for status in statuses if status.state == TO_RECOMPUTE]
        skipped = [status.name for status in statuses if status.state != TO_RECOMPUTE]
        self._run(targets, skipped, force)

    def process_selection(self) -> None:
        """Process the selected acquisitions, up to date or not."""
        targets = [self._statuses[name] for name in self._selected if name in self._statuses]
        self._run(targets, [], True)

    def on_open_folder_requested(self) -> None:
        folder = self._statuses[self._selected[0]].folder if self._selected else self._export_folder
        logger.info("acquisitions.open_folder folder=%s", folder)
        self._view.open_folder(folder)

    def _run(self, targets: List[AcquisitionStatusDTO], skipped: List[str], forced: bool) -> None:
        logger.info(
            "sync.started export=%s scans_found=%d to_process=%d force=%s",
            self._export_folder, len(self._statuses), len(targets), forced,
        )
        for name in skipped:
            logger.debug("scan.up_to_date scan=%s action=none", name)
        batch = _Batch(processed=[], skipped=list(skipped), failed={})
        for status in targets:
            self._process_one(status, batch)

        failures = [f"{name}:{step}" for name, step in batch.failed.items()]
        logger.log(
            logging.WARNING if batch.failed else logging.INFO,
            "sync.finished processed=%d skipped=%d failed=%d failed_scans=%s failures=%s",
            len(batch.processed), len(batch.skipped), len(batch.failed), list(batch.failed), failures,
        )
        self.refresh()
        for listener in self._processed_listeners:
            listener()

    def _process_one(self, status: AcquisitionStatusDTO, batch: _Batch) -> None:
        started = time.monotonic()
        writer: Optional[object] = None
        try:
            parameters = self._parameters_provider()
            logger.info(
                "scan.processing scan=%s reason=%s rotation_angles_deg=%s rotation_origin=%s",
                status.name, status.reason or status.state, getattr(parameters, "rotation_angles", None), self._rotation_origin,
            )
            service, writer = self._processor_factory(status.acquisition_file)
            service.process_scan(ProcessScanDTO(status.csv_file, status.acquisition_file, parameters))
        except Exception as error:
            step = getattr(error, "processing_step", "before_processing")
            batch.failed[status.name] = step
            logger.exception(
                "scan.failed scan=%s error_type=%s step=%s error=%s", status.name, type(error).__name__, step, error
            )
            self._catalog.report_outcome(AcquisitionOutcomeDTO(status.name, False, f"étape {step} : {error}"))
        else:
            batch.processed.append(status.name)
            self._catalog.report_outcome(AcquisitionOutcomeDTO(status.name, True))
            logger.info("scan.processed scan=%s elapsed_s=%.1f", status.name, time.monotonic() - started)
        finally:
            if writer is not None:
                writer.close()

    @staticmethod
    def _row(status: AcquisitionStatusDTO) -> AcquisitionRow:
        if status.state == FAILED:
            detail = status.failure_message or ""
        elif status.state == TO_RECOMPUTE:
            detail = _REASON_LABELS.get(status.reason or "", status.reason or "")
        else:
            detail = ""
        return AcquisitionRow(
            name=status.name,
            kind=_KIND_LABELS.get(status.kind, status.kind),
            measured_object=_measured_object(status.name),
            state=_STATE_LABELS[status.state],
            detail=detail,
        )
