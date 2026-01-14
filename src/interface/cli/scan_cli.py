"""
Scan CLI - JSON-First Interface

Step 8: Interface Layer (The "Headless Controller")
- Expose ScanApplicationService via CLI
- JSON-First (--format json)
- Atomic commands
"""

import json
import sys
import argparse
from typing import Dict, Any, Optional
from pathlib import Path

# Add src to path for imports
# CLI is in src/interface/cli/, so we need to go up 3 levels to get to src/
src_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_dir))

from src.application.services.scan_application_service.scan_application_service import ScanApplicationService
from src.application.services.scan_application_service.ports.i_scan_output_port import IScanOutputPort
from application.dtos.scan_dtos import Scan2DConfigDTO
from domain.models.scan.value_objects.fly_scan_config import FlyScanConfig
from domain.models.scan.value_objects.scan_zone import ScanZone
from domain.models.scan.value_objects.scan_pattern import ScanPattern
from domain.models.test_bench.value_objects.motion_profile import MotionProfile
from domain.models.scan.value_objects.scan_status import ScanStatus


class ScanCLIOutputPort(IScanOutputPort):
    """
    CLI Output Port for ScanApplicationService.
    Implements IScanOutputPort and outputs JSON.
    """
    
    def __init__(self, output_format: str = "json"):
        self.output_format = output_format
        self._events = []
    
    def _output(self, data: Dict[str, Any]) -> None:
        """Output data in specified format."""
        if self.output_format == "json":
            print(json.dumps(data, indent=2))
        else:
            # Human-readable fallback
            print(data)
    
    def present_scan_started(self, scan_id: str, config: Dict[str, Any]) -> None:
        self._output({
            "event": "scan_started",
            "scan_id": scan_id,
            "config": config,
            "timestamp": self._get_timestamp()
        })
    
    def present_scan_progress(self, current_point_index: int, total_points: int, point_data: Any) -> None:
        self._output({
            "event": "scan_progress",
            "current_point": current_point_index,
            "total_points": total_points,
            "progress_percent": (current_point_index / total_points * 100) if total_points > 0 else 0,
            "point_data": point_data,
            "timestamp": self._get_timestamp()
        })
    
    def present_scan_completed(self, scan_id: str, total_points: int) -> None:
        self._output({
            "event": "scan_completed",
            "scan_id": scan_id,
            "total_points": total_points,
            "timestamp": self._get_timestamp()
        })
    
    def present_scan_failed(self, scan_id: str, reason: str) -> None:
        self._output({
            "event": "scan_failed",
            "scan_id": scan_id,
            "reason": reason,
            "timestamp": self._get_timestamp()
        })
    
    def present_scan_cancelled(self, scan_id: str) -> None:
        self._output({
            "event": "scan_cancelled",
            "scan_id": scan_id,
            "timestamp": self._get_timestamp()
        })
    
    def present_scan_paused(self, scan_id: str, current_point_index: int) -> None:
        self._output({
            "event": "scan_paused",
            "scan_id": scan_id,
            "current_point": current_point_index,
            "timestamp": self._get_timestamp()
        })
    
    def present_scan_resumed(self, scan_id: str, resume_from_point_index: int) -> None:
        self._output({
            "event": "scan_resumed",
            "scan_id": scan_id,
            "resume_from_point": resume_from_point_index,
            "timestamp": self._get_timestamp()
        })
    
    # FlyScan methods
    def present_flyscan_started(self, scan_id: str, config: Dict[str, Any]) -> None:
        self._output({
            "event": "flyscan_started",
            "scan_id": scan_id,
            "config": config,
            "timestamp": self._get_timestamp()
        })
    
    def present_flyscan_progress(self, current_point_index: int, total_points: int, point_data: Any) -> None:
        self._output({
            "event": "flyscan_progress",
            "current_point": current_point_index,
            "total_points": total_points,
            "progress_percent": (current_point_index / total_points * 100) if total_points > 0 else 0,
            "point_data": point_data,
            "timestamp": self._get_timestamp()
        })
    
    def present_flyscan_completed(self, scan_id: str, total_points: int) -> None:
        self._output({
            "event": "flyscan_completed",
            "scan_id": scan_id,
            "total_points": total_points,
            "timestamp": self._get_timestamp()
        })
    
    def present_flyscan_failed(self, scan_id: str, reason: str) -> None:
        self._output({
            "event": "flyscan_failed",
            "scan_id": scan_id,
            "reason": reason,
            "timestamp": self._get_timestamp()
        })
    
    def present_flyscan_cancelled(self, scan_id: str) -> None:
        self._output({
            "event": "flyscan_cancelled",
            "scan_id": scan_id,
            "timestamp": self._get_timestamp()
        })
    
    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().isoformat()


def create_scan_service() -> ScanApplicationService:
    """
    Create ScanApplicationService with mock adapters.
    Composition root for CLI.
    """
    from infrastructure.events.in_memory_event_bus import InMemoryEventBus
    from infrastructure.execution.step_scan_executor import StepScanExecutor
    from infrastructure.mocks.adapter_mock_i_motion_port import MockMotionPort
    from infrastructure.mocks.adapter_mock_i_acquisition_port import MockAcquisitionPort
    from infrastructure.mocks.adapter_mock_fly_scan_executor import MockFlyScanExecutor
    
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
    
    return service


def cmd_scan_start(args: argparse.Namespace) -> int:
    """Start a StepScan."""
    output_format = args.format or "json"
    cli_output = ScanCLIOutputPort(output_format=output_format)
    
    # Parse config from JSON file or stdin
    if args.config:
        with open(args.config, 'r') as f:
            config_data = json.load(f)
    elif not sys.stdin.isatty():
        config_data = json.load(sys.stdin)
    else:
        print(json.dumps({"error": "No config provided. Use --config or pipe JSON to stdin."}, indent=2))
        return 1
    
    try:
        # Create DTO from JSON
        dto = Scan2DConfigDTO(
            x_min=float(config_data["x_min"]),
            x_max=float(config_data["x_max"]),
            y_min=float(config_data["y_min"]),
            y_max=float(config_data["y_max"]),
            x_nb_points=int(config_data["x_nb_points"]),
            y_nb_points=int(config_data["y_nb_points"]),
            scan_pattern=config_data.get("scan_pattern", "SERPENTINE"),
            stabilization_delay_ms=int(config_data.get("stabilization_delay_ms", 300)),
            averaging_per_position=int(config_data.get("averaging_per_position", 10)),
            uncertainty_volts=float(config_data.get("uncertainty_volts", 0.001)),
            motion_speed_mm_s=config_data.get("motion_speed_mm_s")
        )
        
        # Create service and set output port
        service = create_scan_service()
        service.set_output_port(cli_output)
        
        # Service already forwards events to output port via _on_domain_event
        # No need to subscribe again (would cause duplicates)
        
        # Execute scan
        success = service.execute_scan(dto)
        
        if not success:
            print(json.dumps({"error": "Failed to start scan"}, indent=2))
            return 1
        
        # Wait for completion (blocking for CLI)
        import time
        timeout = args.timeout or 300.0
        start_time = time.time()
        
        while service.get_status().status != ScanStatus.COMPLETED.value:
            if time.time() - start_time > timeout:
                print(json.dumps({"error": f"Scan timeout after {timeout}s"}, indent=2))
                return 1
            if service.get_status().status in (ScanStatus.FAILED.value, ScanStatus.CANCELLED.value):
                status = service.get_status()
                print(json.dumps({"error": f"Scan {status.status}"}, indent=2))
                return 1
            time.sleep(0.1)
        
        return 0
        
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))
        return 1


def cmd_flyscan_start(args: argparse.Namespace) -> int:
    """Start a FlyScan."""
    output_format = args.format or "json"
    cli_output = ScanCLIOutputPort(output_format=output_format)
    
    # Parse config from JSON file or stdin
    if args.config:
        with open(args.config, 'r') as f:
            config_data = json.load(f)
    elif not sys.stdin.isatty():
        config_data = json.load(sys.stdin)
    else:
        print(json.dumps({"error": "No config provided. Use --config or pipe JSON to stdin."}, indent=2))
        return 1
    
    try:
        # Create FlyScanConfig from JSON
        motion_profile = MotionProfile(
            min_speed=float(config_data["motion_profile"]["min_speed"]),
            target_speed=float(config_data["motion_profile"]["target_speed"]),
            acceleration=float(config_data["motion_profile"]["acceleration"]),
            deceleration=float(config_data["motion_profile"]["deceleration"])
        )
        
        config = FlyScanConfig(
            scan_zone=ScanZone(
                x_min=float(config_data["scan_zone"]["x_min"]),
                x_max=float(config_data["scan_zone"]["x_max"]),
                y_min=float(config_data["scan_zone"]["y_min"]),
                y_max=float(config_data["scan_zone"]["y_max"])
            ),
            x_nb_points=int(config_data["x_nb_points"]),
            y_nb_points=int(config_data["y_nb_points"]),
            scan_pattern=ScanPattern[config_data.get("scan_pattern", "SERPENTINE")],
            motion_profile=motion_profile,
            desired_acquisition_rate_hz=float(config_data.get("desired_acquisition_rate_hz", 100.0)),
            max_spatial_gap_mm=float(config_data.get("max_spatial_gap_mm", 0.5))
        )
        
        acquisition_rate_hz = float(config_data.get("acquisition_rate_hz", config.desired_acquisition_rate_hz))
        
        # Create service and set output port
        service = create_scan_service()
        service.set_output_port(cli_output)
        
        # Service already forwards events to output port via _on_flyscan_event
        # No need to subscribe again (would cause duplicates)
        
        # Execute FlyScan
        success = service.execute_fly_scan(config, acquisition_rate_hz)
        
        if not success:
            print(json.dumps({"error": "Failed to start FlyScan"}, indent=2))
            return 1
        
        # Wait for completion (blocking for CLI)
        import time
        timeout = args.timeout or 300.0
        start_time = time.time()
        
        while service._current_fly_scan and not service._current_fly_scan.status.is_final():
            if time.time() - start_time > timeout:
                print(json.dumps({"error": f"FlyScan timeout after {timeout}s"}, indent=2))
                return 1
            time.sleep(0.1)
        
        return 0
        
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))
        return 1


def cmd_scan_status(args: argparse.Namespace) -> int:
    """Get scan status."""
    output_format = args.format or "json"
    
    # For CLI, we'd need to persist service state or use a different mechanism
    # For now, return "no active scan"
    status_data = {
        "status": "no_active_scan",
        "message": "CLI status requires persistent service state (not implemented)"
    }
    
    if output_format == "json":
        print(json.dumps(status_data, indent=2))
    else:
        print(status_data)
    
    return 0


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="AEFI Scan CLI - JSON-First Interface")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format")
    
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # scan start
    scan_start = subparsers.add_parser("scan-start", help="Start a StepScan")
    scan_start.add_argument("--config", type=str, help="JSON config file path")
    scan_start.add_argument("--timeout", type=float, default=300.0, help="Timeout in seconds")
    
    # flyscan start
    flyscan_start = subparsers.add_parser("flyscan-start", help="Start a FlyScan")
    flyscan_start.add_argument("--config", type=str, help="JSON config file path")
    flyscan_start.add_argument("--timeout", type=float, default=300.0, help="Timeout in seconds")
    
    # scan status
    scan_status = subparsers.add_parser("scan-status", help="Get scan status")
    
    args = parser.parse_args()
    
    if args.command == "scan-start":
        return cmd_scan_start(args)
    elif args.command == "flyscan-start":
        return cmd_flyscan_start(args)
    elif args.command == "scan-status":
        return cmd_scan_status(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())

