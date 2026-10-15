"""
Fly-line preview overlay: the provisional points of a fly line disappear from the map when the
line is not confirmed (abandoned, scan cancelled or failed). See fly_line_preview_overlay_intention.md.
"""
import logging
from typing import Any, Dict, List, Sequence, Tuple

logger = logging.getLogger(__name__)


class FlyLinePreviewOverlay:
    """Draws the preview points and remembers those not yet confirmed by a definitive point."""

    def __init__(self, panels: Sequence[Any]):
        self._panels = list(panels)
        # ponytail: keyed by exact (x, y) — the preview and the definitive point of a grid point
        # carry the same position object on the service side; switch to (line, index) if they ever differ.
        self._unconfirmed: Dict[Tuple[float, float], List[str]] = {}

    def reset(self, *_args) -> None:
        self._unconfirmed.clear()

    def show_preview(self, line_index: int, index_in_line: int, data: Dict[str, Any]) -> None:
        # Same drawing by position as the definitive point, which overwrites it at the line commit.
        self._unconfirmed[(data["x"], data["y"])] = list(data["value"])
        for panel in self._panels:
            panel.update_data_point_from_position(data["x"], data["y"], data["value"], redraw=False)

    def confirm(self, _current: int, _total: int, data: Dict[str, Any]) -> None:
        self._unconfirmed.pop((data["x"], data["y"]), None)

    def discard(self, why: str) -> None:
        if not self._unconfirmed:
            logger.info("FlyLinePreviewOverlay: %s, no unconfirmed preview point. Doing nothing.", why)
            return
        logger.info("FlyLinePreviewOverlay: %s, erasing %d unconfirmed preview point(s)", why, len(self._unconfirmed))
        for (x, y), channels in self._unconfirmed.items():
            blank = {channel: float("nan") for channel in channels}
            for panel in self._panels:
                panel.update_data_point_from_position(x, y, blank, redraw=False)
        self._unconfirmed.clear()


def wire_fly_line_preview(scan_presenter: Any, panels: Sequence[Any]) -> FlyLinePreviewOverlay:
    """Connect the ScanPresenter signals to an overlay over `panels` (returned, kept alive by the closures)."""
    overlay = FlyLinePreviewOverlay(panels)
    scan_presenter.scan_started.connect(overlay.reset)
    scan_presenter.scan_line_preview.connect(overlay.show_preview)
    scan_presenter.scan_progress.connect(overlay.confirm)
    scan_presenter.scan_line_abandoned.connect(
        lambda line_index, reason: overlay.discard(f"line {line_index} abandoned ({reason})")
    )
    scan_presenter.scan_cancelled.connect(lambda _scan_id: overlay.discard("scan cancelled"))
    scan_presenter.scan_failed.connect(lambda reason: overlay.discard(f"scan failed ({reason})"))
    return overlay
