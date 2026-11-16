import h5py
import numpy as np

from ....domain.processing._tests.synthetic_scan_generator import SyntheticScanGenerator
from ....application.post_processing_service.dtos.process_scan_dto import ProcessScanDTO
from ....domain.processing.processing_steps.processing_steps import STEP_NAMES, ProcessingParameters
from ..headless_wiring import build_post_processing_service


def _write_scan_csv(path):
    generator = SyntheticScanGenerator(grid_size=10, scan_range=10.0)
    data = generator.generate_base_signal()
    lines = ["x,y,voltage_x_in_phase,voltage_x_quadrature,voltage_y_in_phase,voltage_y_quadrature,"
             "voltage_z_in_phase,voltage_z_quadrature"]
    for row in generator.to_rows(data):
        lines.append(",".join(repr(float(row[k])) for k in
                              ("x", "y", "voltage_x_in_phase", "voltage_x_quadrature", "voltage_y_in_phase",
                               "voltage_y_quadrature", "voltage_z_in_phase", "voltage_z_quadrature")))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_the_wired_service_writes_the_five_steps_in_the_acquisition_file(tmp_path):
    csv = tmp_path / "scan_aefi.csv"
    acquisition = tmp_path / "scan.h5"
    _write_scan_csv(csv)

    service, writer = build_post_processing_service(str(acquisition))
    summary = service.process_scan(ProcessScanDTO(str(csv), str(acquisition), ProcessingParameters(rotation_angles=(0.0, 0.0, 45.0))))
    writer.close()

    assert summary.success is True
    with h5py.File(acquisition, "r") as h5:
        assert sorted(h5.keys()) == sorted(STEP_NAMES)
        assert np.asarray(h5["interpolated"]["data"]).shape[:2] == (200, 200)
