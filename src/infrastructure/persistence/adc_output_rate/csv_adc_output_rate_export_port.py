"""
CSV ADC Output Rate Export Port

See csv_adc_output_rate_export_port_intention.md.
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, Sequence, Tuple

import numpy as np

from application.services.adc_output_rate_characterization_service.dtos.adc_output_rate_dtos import (
    AdcOutputRateCharacterizationDTO,
    DrdyCaptureDTO,
)
from application.services.adc_output_rate_characterization_service.ports.i_adc_output_rate_export_port import (
    IAdcOutputRateExportPort,
)
from domain.shared_kernel.operation_result import OperationResult

logger = logging.getLogger(__name__)


class CsvAdcOutputRateExportPort(IAdcOutputRateExportPort):
    def __init__(self, base_output_dir: Optional[Path] = None, clock: Callable[[], datetime] = datetime.now) -> None:
        self._base = base_output_dir or Path.home() / "Desktop" / "AEFI_Acquisition_Exports"
        self._clock = clock

    def export(
        self, result: AdcOutputRateCharacterizationDTO, captures: Sequence[Tuple[int, DrdyCaptureDTO]]
    ) -> OperationResult[str, str]:
        stamp = self._clock().strftime("%Y-%m-%d_%H%M%S")
        folder = self._base / f"{stamp}_odr-adc-ads131a04-drdy-oscilloscope"
        prefix = f"{stamp}_odr-drdy"
        try:
            folder.mkdir(parents=True)
            self._write_summary(folder / f"{prefix}_resume-par-osr.csv", result)
            self._write_intervals(folder / f"{prefix}_intervalles-fronts-descendants.csv", captures)
            waveforms = {}
            for osr, capture in captures:
                if capture.waveform_t_s:
                    waveforms[f"osr_{osr}_t_s"] = np.asarray(capture.waveform_t_s)
                    waveforms[f"osr_{osr}_v_V"] = np.asarray(capture.waveform_v)
            if waveforms:
                np.savez_compressed(folder / f"{prefix}_formes-d-onde.npz", **waveforms)
        except OSError as error:
            logger.warning("CsvAdcOutputRateExportPort: export to %s failed: %s", folder, error)
            return OperationResult.fail(f"export impossible ({folder}) : {error}")
        logger.info("CsvAdcOutputRateExportPort: %d capture(s) exported to %s", len(captures), folder)
        return OperationResult.ok(str(folder))

    @staticmethod
    def _write_summary(path: Path, result: AdcOutputRateCharacterizationDTO) -> None:
        with open(path, "w", newline="", encoding="utf-8") as f:
            for key, value in (
                ("instrument", result.instrument),
                ("mean_modulator_frequency_hz", result.mean_modulator_frequency_hz),
                ("max_modulator_frequency_relative_deviation", result.max_modulator_frequency_relative_deviation),
                ("restored_oversampling_ratio", result.restored_oversampling_ratio),
            ):
                f.write(f"# {key},{value}\n")
            writer = csv.writer(f)
            writer.writerow(["oversampling_ratio", "output_rate_hz", "mean_interval_s", "interval_std_s",
                             "median_interval_s", "regular_interval_count", "irregular_interval_count",
                             "implied_modulator_frequency_hz"])
            for p in result.points:
                writer.writerow([p.oversampling_ratio, p.output_rate_hz, p.mean_interval_s, p.interval_std_s,
                                 p.median_interval_s, p.regular_interval_count, p.irregular_interval_count,
                                 p.implied_modulator_frequency_hz])

    @staticmethod
    def _write_intervals(path: Path, captures: Sequence[Tuple[int, DrdyCaptureDTO]]) -> None:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["oversampling_ratio", "interval_index", "interval_s", "sample_interval_s"])
            for osr, capture in captures:
                for i, interval in enumerate(np.diff(capture.falling_edge_times_s)):
                    writer.writerow([osr, i, float(interval), capture.sample_interval_s])
