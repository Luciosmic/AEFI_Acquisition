"""
Test ScanPresenter Connection

Verifies that ScanPresenter is correctly connected to ScanApplicationService
using the same pattern as CLI (IScanOutputPort).

Since CLI is intensively tested and works, this validates that the presenter
uses the same validated controller pattern.
"""

import unittest
from unittest.mock import Mock, MagicMock
from domain.models.scan.value_objects.scan_status import ScanStatus
from src.application.services.scan_application_service.ports.i_scan_output_port import IScanOutputPort


class TestScanPresenterConnection(unittest.TestCase):
    """Test that ScanPresenter is correctly connected to service."""
    
    def test_presenter_implements_output_port(self):
        """Verify ScanPresenter implements IScanOutputPort."""
        from interface.presenters.scan_presenter import ScanPresenter
        
        # Check inheritance
        self.assertTrue(issubclass(ScanPresenter, IScanOutputPort),
                       "ScanPresenter must implement IScanOutputPort")
        
        # Check all required methods exist
        required_methods = [
            'present_scan_started',
            'present_scan_progress',
            'present_scan_completed',
            'present_scan_failed',
            'present_scan_cancelled',
            'present_scan_paused',
            'present_scan_resumed',
            'present_flyscan_started',
            'present_flyscan_progress',
            'present_flyscan_completed',
            'present_flyscan_failed',
            'present_flyscan_cancelled'
        ]
        
        for method_name in required_methods:
            self.assertTrue(hasattr(ScanPresenter, method_name),
                          f"ScanPresenter must implement {method_name}")
    
    def test_presenter_sets_output_port_on_service(self):
        """Verify presenter registers itself as output port."""
        from interface.presenters.scan_presenter import ScanPresenter
        from src.application.services.scan_application_service.scan_application_service import ScanApplicationService
        
        # Create mocks
        mock_service = Mock(spec=ScanApplicationService)
        mock_export_service = Mock()
        mock_event_bus = Mock()
        mock_transformation_service = Mock()
        mock_transformation_service.get_rotation_angles.return_value = [0, 0, 0]
        
        # Create presenter
        presenter = ScanPresenter(
            service=mock_service,
            export_service=mock_export_service,
            event_bus=mock_event_bus,
            transformation_service=mock_transformation_service
        )
        
        # Verify set_output_port was called
        mock_service.set_output_port.assert_called_once_with(presenter)
    
    def test_presenter_receives_events_from_service(self):
        """Verify presenter receives events when service calls output port."""
        from interface.presenters.scan_presenter import ScanPresenter
        from src.application.services.scan_application_service.scan_application_service import ScanApplicationService
        from infrastructure.events.in_memory_event_bus import InMemoryEventBus
        from infrastructure.execution.step_scan_executor import StepScanExecutor
        from infrastructure.mocks.adapter_mock_i_motion_port import MockMotionPort
        from infrastructure.mocks.adapter_mock_i_acquisition_port import MockAcquisitionPort
        from infrastructure.mocks.adapter_mock_fly_scan_executor import MockFlyScanExecutor
        from src.application.services.scan_application_service.scan_export_service import ScanExportService
        from application.services.transformation_service.transformation_service import TransformationService
        from application.dtos.scan_dtos import Scan2DConfigDTO
        
        # Create real service (same as CLI uses)
        event_bus = InMemoryEventBus()
        motion_port = MockMotionPort(event_bus=event_bus, motion_delay_ms=10.0)
        acquisition_port = MockAcquisitionPort()
        scan_executor = StepScanExecutor(motion_port, acquisition_port, event_bus)
        fly_scan_executor = MockFlyScanExecutor()
        
        service = ScanApplicationService(
            motion_port=motion_port,
            acquisition_port=acquisition_port,
            event_bus=event_bus,
            scan_executor=scan_executor,
            fly_scan_executor=fly_scan_executor
        )
        
        # Create presenter
        export_service = ScanExportService(event_bus, Mock(), Mock())
        transformation_service = TransformationService(event_bus)
        
        presenter = ScanPresenter(
            service=service,
            export_service=export_service,
            event_bus=event_bus,
            transformation_service=transformation_service
        )
        
        # Verify presenter is set as output port
        self.assertEqual(service._output_port, presenter,
                        "Service should have presenter as output port")
        
        # Track signals emitted
        signals_received = []
        
        def on_scan_started(scan_id, config):
            signals_received.append(('scan_started', scan_id, config))
        
        def on_scan_progress(current, total, data):
            signals_received.append(('scan_progress', current, total))
        
        def on_scan_completed(total_points):
            signals_received.append(('scan_completed', total_points))
        
        presenter.scan_started.connect(on_scan_started)
        presenter.scan_progress.connect(on_scan_progress)
        presenter.scan_completed.connect(on_scan_completed)
        
        # Execute a scan (same as CLI would)
        dto = Scan2DConfigDTO(
            x_min=0.0,
            x_max=5.0,
            y_min=0.0,
            y_max=5.0,
            x_nb_points=2,
            y_nb_points=2,
            scan_pattern="RASTER",
            stabilization_delay_ms=100,
            averaging_per_position=1,
            uncertainty_volts=0.001
        )
        
        success = service.execute_scan(dto)
        self.assertTrue(success, "Scan should start successfully")
        
        # Wait for completion
        import time
        timeout = 10.0
        start_time = time.time()
        while service.get_status().status != ScanStatus.COMPLETED.value:
            if time.time() - start_time > timeout:
                break
            if service.get_status().status in (ScanStatus.FAILED.value, ScanStatus.CANCELLED.value):
                break
            time.sleep(0.1)
        
        # Verify signals were received (presenter received events from service)
        self.assertGreater(len(signals_received), 0,
                          "Presenter should receive events from service")
        
        # Verify scan_started was received
        started_events = [s for s in signals_received if s[0] == 'scan_started']
        self.assertGreater(len(started_events), 0,
                          "Presenter should receive scan_started event")
    
    def test_presenter_same_pattern_as_cli(self):
        """Verify presenter uses same connection pattern as CLI."""
        from interface.presenters.scan_presenter import ScanPresenter
        from interface.cli.scan_cli import ScanCLIOutputPort
        
        # Both implement IScanOutputPort
        self.assertTrue(issubclass(ScanPresenter, IScanOutputPort))
        # ScanCLIOutputPort doesn't explicitly inherit, but implements interface
        # Check that both have same methods
        presenter_methods = {m for m in dir(ScanPresenter) if m.startswith('present_')}
        cli_methods = {m for m in dir(ScanCLIOutputPort) if m.startswith('present_')}
        
        # Core methods should match
        core_methods = {
            'present_scan_started',
            'present_scan_progress',
            'present_scan_completed',
            'present_scan_failed',
            'present_scan_cancelled'
        }
        
        for method in core_methods:
            self.assertIn(method, presenter_methods,
                         f"Presenter must have {method} (same as CLI)")
            self.assertIn(method, cli_methods,
                         f"CLI must have {method} (same as Presenter)")


if __name__ == '__main__':
    unittest.main()

