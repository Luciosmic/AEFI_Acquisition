"""ScanPresenter routes a 'line' start request to execute_line_scan."""
from application.services.scan_application_service.dtos.scan_dtos import LineScanConfigDTO, Scan2DConfigDTO
from interface.presenters.scan_presenter import ScanPresenter


class _FakeScanService:
    def __init__(self):
        self.calls = []

    def set_output_port(self, port):
        pass

    def execute_scan(self, dto):
        self.calls.append(dto)
        return True

    def execute_line_scan(self, dto):
        self.calls.append(dto)
        return True


class _FakeExportService:
    def configure_export(self, dto):
        pass


def _presenter():
    service = _FakeScanService()
    return ScanPresenter(service, _FakeExportService(), event_bus=None), service


def test_line_request_calls_execute_line_scan():
    presenter, service = _presenter()
    presenter.on_scan_start_requested({
        "scan_kind": "line",
        "line_center_x": "650", "line_center_y": "700", "line_length_mm": "120",
        "line_n_points": "41", "line_theta_deg": "45",
        "stabilization_delay_ms": "200", "averaging_per_position": "5",
        "differential_mode": True, "differential_settle_delay_ms": "30",
    })
    assert service.calls == [LineScanConfigDTO(
        center_x=650.0, center_y=700.0, length_mm=120.0, n_points=41, theta_deg=45.0,
        stabilization_delay_ms=200, averaging_per_position=5,
        differential_mode=True, differential_settle_delay_ms=30.0,
    )]


def test_request_without_kind_stays_a_grid_scan():
    presenter, service = _presenter()
    presenter.on_scan_start_requested({})
    assert isinstance(service.calls[0], Scan2DConfigDTO)
