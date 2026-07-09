from abc import ABC, abstractmethod
from typing import Any, Dict


class IScanOutputPort(ABC):
    """
    Output Port for Scan Application Service.

    Responsibility:
    - Defines the contract for presenting scan lifecycle events to the UI or any adapter.

    Rationale:
    - Decouples orchestration logic (ScanApplicationService) from rendering concerns.
    - Implemented by Presenters (PySide6) or CLI/test adapters.

    Design:
    - Pure ABC — no state, no implementation logic.
    - Implemented by infrastructure/interface adapters (e.g. ScanPresenter).
    """

    @abstractmethod
    def present_scan_started(self, scan_id: str, config: Dict[str, Any]) -> None: ...

    @abstractmethod
    def present_scan_progress(self, current_point_index: int, total_points: int, point_data: Any) -> None: ...

    @abstractmethod
    def present_scan_completed(self, scan_id: str, total_points: int) -> None: ...

    @abstractmethod
    def present_scan_failed(self, scan_id: str, reason: str) -> None: ...

    @abstractmethod
    def present_scan_cancelled(self, scan_id: str) -> None: ...

    @abstractmethod
    def present_scan_paused(self, scan_id: str, current_point_index: int) -> None: ...

    @abstractmethod
    def present_scan_resumed(self, scan_id: str, resume_from_point_index: int) -> None: ...
