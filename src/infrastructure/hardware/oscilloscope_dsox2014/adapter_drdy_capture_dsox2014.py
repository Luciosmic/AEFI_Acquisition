"""
DRDY Capture Adapter — Agilent DSO-X 2014A (VISA/SCPI)

See adapter_drdy_capture_dsox2014_intention.md.
"""

import logging
from typing import Callable, Optional, Tuple

import numpy as np

from application.services.adc_output_rate_characterization_service.dtos.adc_output_rate_dtos import (
    DrdyCaptureDTO,
    DrdyCaptureRequestDTO,
)
from application.services.adc_output_rate_characterization_service.ports.i_drdy_capture_port import IDrdyCapturePort
from domain.shared_kernel.operation_result import OperationResult

logger = logging.getLogger(__name__)

INSTRUMENT_MODEL = "DSO-X 2014A"
LOGIC_HIGH_V = 3.3  # IOVDD (datasheet ADS131A04): trigger level and vertical scale
TIMEOUT_MS = 20000
_RUN_BIT = 1 << 3  # :OPERegister:CONDition? bit 3 = acquisition running


def falling_edges(t: np.ndarray, v: np.ndarray, sample_interval_s: float) -> np.ndarray:
    """Falling crossings of the mid-level (min+max)/2, linearly interpolated."""
    threshold = (v.min() + v.max()) / 2
    above = v > threshold
    idx = np.where(above[:-1] & ~above[1:])[0]
    return t[idx] + (v[idx] - threshold) / (v[idx] - v[idx + 1]) * sample_interval_s


class AdapterDrdyCaptureDsox2014(IDrdyCapturePort):
    def __init__(self, visa_address: Optional[str] = None, resource_manager_factory: Optional[Callable] = None) -> None:
        """`visa_address`: None = first VISA instrument whose *IDN? names the
        DSO-X 2014A. `resource_manager_factory`: pyvisa.ResourceManager (tests inject a stub)."""
        self._visa_address = visa_address
        self._rm_factory = resource_manager_factory

    def capture_falling_edges(self, request: DrdyCaptureRequestDTO) -> OperationResult[DrdyCaptureDTO, str]:
        logger.info(
            "AdapterDrdyCaptureDsox2014: capture channel=%d probe=%g window=%.3e s",
            request.scope_channel, request.probe_ratio, request.window_s,
        )
        try:
            scope = self._open()
        except Exception as error:  # VISA library missing, no instrument, I/O error
            logger.warning("AdapterDrdyCaptureDsox2014: no oscilloscope: %s", error)
            return OperationResult.fail(f"oscilloscope {INSTRUMENT_MODEL} indisponible : {error}")
        try:
            idn = scope.query("*IDN?").strip()
            saved_setup = scope.query_binary_values(":SYSTem:SETup?", datatype="B", container=bytes)
            try:
                t, v, x_inc = self._acquire(scope, request)
            finally:
                scope.write_binary_values(":SYSTem:SETup ", list(saved_setup), datatype="B")
        except Exception as error:  # SCPI/VISA error, trigger timeout
            logger.warning("AdapterDrdyCaptureDsox2014: capture failed: %s", error)
            return OperationResult.fail(f"capture impossible ({type(error).__name__}) : {error}")
        finally:
            try:
                scope.close()
            except Exception:
                logger.debug("AdapterDrdyCaptureDsox2014: close failed", exc_info=True)
        edges = falling_edges(t, v, x_inc)
        logger.info("AdapterDrdyCaptureDsox2014: %d falling edges, sample interval %.3e s", len(edges), x_inc)
        return OperationResult.ok(DrdyCaptureDTO(
            falling_edge_times_s=tuple(float(e) for e in edges),
            sample_interval_s=x_inc,
            instrument=idn,
            waveform_t_s=tuple(t.tolist()),
            waveform_v=tuple(v.tolist()),
        ))

    def _open(self):
        import pyvisa

        rm = (self._rm_factory or pyvisa.ResourceManager)()
        address = self._visa_address
        if address is None:
            for candidate in rm.list_resources():
                if not candidate.startswith(("USB", "TCPIP")):
                    continue
                probe = rm.open_resource(candidate)
                try:
                    probe.timeout = 2000
                    if INSTRUMENT_MODEL in probe.query("*IDN?"):
                        address = candidate
                        break
                finally:
                    probe.close()
            if address is None:
                raise RuntimeError("aucun oscilloscope VISA détecté (USB/TCPIP)")
        scope = rm.open_resource(address)
        scope.timeout = TIMEOUT_MS
        return scope

    @staticmethod
    def _acquire(scope, request: DrdyCaptureRequestDTO) -> Tuple[np.ndarray, np.ndarray, float]:
        ch = f":CHANnel{request.scope_channel}"
        scope.write("*CLS")
        scope.write(f"{ch}:DISPlay ON")
        scope.write(f"{ch}:PROBe {request.probe_ratio}")
        scope.write(f"{ch}:COUPling DC")
        scope.write(f"{ch}:SCALe {LOGIC_HIGH_V / 4}")
        scope.write(f"{ch}:OFFSet {LOGIC_HIGH_V / 2}")
        scope.write(f":TIMebase:SCALe {request.window_s / 10}")
        scope.write(":TIMebase:REFerence LEFT")
        scope.write(":ACQuire:TYPE NORMal")
        scope.write(":TRIGger:MODE EDGE")
        scope.write(f":TRIGger:EDGE:SOURce CHANnel{request.scope_channel}")
        scope.write(":TRIGger:EDGE:SLOPe NEGative")
        scope.write(f":TRIGger:EDGE:LEVel {LOGIC_HIGH_V / 2}")
        scope.write(":SINGle")
        scope.query("*OPC?")
        for _ in range(200):
            if int(scope.query(":OPERegister:CONDition?")) & _RUN_BIT == 0:
                break
            scope.query("*OPC?")
        scope.write(f":WAVeform:SOURce CHANnel{request.scope_channel}")
        scope.write(":WAVeform:FORMat BYTE")
        scope.write(":WAVeform:POINts:MODE RAW")
        scope.write(":WAVeform:POINts MAX")
        pre = scope.query(":WAVeform:PREamble?").strip().split(",")
        x_inc, x_org, x_ref = float(pre[4]), float(pre[5]), float(pre[6])
        y_inc, y_org, y_ref = float(pre[7]), float(pre[8]), float(pre[9])
        raw = scope.query_binary_values(":WAVeform:DATA?", datatype="B", container=np.array)
        t = (np.arange(len(raw)) - x_ref) * x_inc + x_org
        v = (raw.astype(float) - y_ref) * y_inc + y_org
        return t, v, x_inc
