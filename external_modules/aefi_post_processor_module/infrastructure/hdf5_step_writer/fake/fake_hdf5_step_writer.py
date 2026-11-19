"""
FakeHdf5StepWriter - Keeps the steps in memory (see fake_hdf5_step_writer_intention.md).
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ....application.post_processing_service.dtos.scan_samples_dto import ScanSamplesDTO
from ....application.post_processing_service.dtos.source_record_dto import SourceRecordDTO
from ....application.post_processing_service.ports.i_step_writer import IStepWriter


class FakeHdf5StepWriter(IStepWriter):
    def __init__(self) -> None:
        self.source: Optional[SourceRecordDTO] = None
        self.raw_scan: Optional[ScanSamplesDTO] = None
        self.closed = False
        self._steps: Dict[str, Tuple[np.ndarray, Dict[str, Any]]] = {}
        self._history: List[str] = []

    def record_source(self, source: SourceRecordDTO) -> None:
        self.source = source

    def save_raw_scan(self, samples: ScanSamplesDTO) -> None:
        self.raw_scan = samples

    def save_step(self, step_name: str, data: np.ndarray, metadata: Dict[str, Any]) -> None:
        self._steps[step_name] = (np.array(data), dict(metadata or {}))
        self._history.append(f"{step_name} @ {datetime.now().isoformat()}")

    def load_step(self, step_name: str) -> Tuple[np.ndarray, Dict[str, Any]]:
        if step_name not in self._steps:
            raise KeyError(f"Processing step '{step_name}' not found in HDF5 file.")
        data, metadata = self._steps[step_name]
        return np.array(data), dict(metadata)

    def processing_history(self) -> List[str]:
        return list(self._history)

    def close(self) -> None:
        self.closed = True
