import unittest

import numpy as np

from application.services.adc_output_rate_characterization_service.dtos.adc_output_rate_dtos import (
    DrdyCaptureRequestDTO,
)
from infrastructure.hardware.oscilloscope_dsox2014.adapter_drdy_capture_dsox2014 import (
    AdapterDrdyCaptureDsox2014,
    falling_edges,
)

SAMPLE = 5e-7


def drdy_waveform(period=1e-3, pulse=4e-5, count=10):
    t = np.arange(int(count * period / SAMPLE)) * SAMPLE
    v = np.where((t % period) < pulse, 0.0, 3.1)
    return t, v


class StubScope:
    """Minimal DSO-X answering the adapter's SCPI with a synthetic DRDY."""

    def __init__(self, t, v):
        self._t, self._v = t, v
        self.writes, self.closed, self.setup_restored = [], False, False

    def write(self, command):
        self.writes.append(command)

    def query(self, command):
        if command == "*IDN?":
            return "AGILENT TECHNOLOGIES,DSO-X 2014A,MY0,1\n"
        if command == ":OPERegister:CONDition?":
            return "0"
        if command == ":WAVeform:PREamble?":
            return f"0,0,{len(self._t)},1,{SAMPLE},0,0,{3.1 / 255},0,0"
        return "1"

    def query_binary_values(self, command, datatype, container):
        if command == ":SYSTem:SETup?":
            return b"SETUP"
        return container(np.round(self._v / (3.1 / 255)).astype(int).tolist())

    def write_binary_values(self, command, values, datatype):
        self.setup_restored = bytes(values) == b"SETUP"

    def close(self):
        self.closed = True


class StubResourceManager:
    def __init__(self, scope):
        self.scope = scope

    def list_resources(self):
        return ("ASRL10::INSTR", "USB0::0x0957::0x1798::MY0::INSTR")

    def open_resource(self, address):
        return self.scope


class TestFallingEdges(unittest.TestCase):
    def test_edges_are_one_period_apart(self):
        t, v = drdy_waveform()
        edges = falling_edges(t, v, SAMPLE)
        self.assertEqual(len(edges), 9)  # the first low level starts at t=0: not a falling crossing
        np.testing.assert_allclose(np.diff(edges), 1e-3, atol=SAMPLE)


class TestAdapterDrdyCaptureDsox2014(unittest.TestCase):
    def test_captures_edges_and_restores_the_instrument(self):
        scope = StubScope(*drdy_waveform())
        adapter = AdapterDrdyCaptureDsox2014(resource_manager_factory=lambda: StubResourceManager(scope))

        result = adapter.capture_falling_edges(DrdyCaptureRequestDTO(scope_channel=1, probe_ratio=10, window_s=0.01))

        self.assertTrue(result.is_success)
        self.assertEqual(len(result.value.falling_edge_times_s), 9)
        self.assertIn("DSO-X 2014A", result.value.instrument)
        self.assertIn(":TIMebase:SCALe 0.001", scope.writes)
        self.assertTrue(scope.setup_restored)
        self.assertTrue(scope.closed)

    def test_no_instrument_is_a_failure_not_an_exception(self):
        class Empty:
            def list_resources(self):
                return ("ASRL10::INSTR",)

        adapter = AdapterDrdyCaptureDsox2014(resource_manager_factory=Empty)
        result = adapter.capture_falling_edges(DrdyCaptureRequestDTO(1, 10, 0.05))
        self.assertTrue(result.is_failure)
        self.assertIn("aucun oscilloscope", result.error)


if __name__ == "__main__":
    unittest.main()
