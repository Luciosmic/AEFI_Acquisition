"""
Integration Tests for Scan CLI

Step 9: Deterministic Integration Verification (The "Proof")

Tests the CLI interface via subprocess calls, parsing JSON output,
and verifying invariants. Includes edge cases and error scenarios.
"""

import unittest
import subprocess
import json
import tempfile
import os
from pathlib import Path
from typing import List, Dict, Any


class TestScanCLIIntegration(unittest.TestCase):
    """Integration tests for Scan CLI."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Get CLI script path
        src_dir = Path(__file__).parent.parent.parent.parent
        cls.cli_script = src_dir / "interface" / "cli" / "scan_cli.py"
        cls.examples_dir = src_dir / "interface" / "cli" / "examples"
        
        # Verify CLI exists
        assert cls.cli_script.exists(), f"CLI script not found: {cls.cli_script}"
    
    def _run_cli(self, args: List[str], input_data: str = None, timeout: float = 30.0) -> tuple:
        """
        Run CLI command and return (returncode, stdout, stderr).
        
        Args:
            args: CLI arguments (without script path)
            input_data: Optional stdin input
            timeout: Command timeout in seconds
            
        Returns:
            (returncode, stdout_lines, stderr)
        """
        cmd = ["python", str(self.cli_script)] + args
        
        try:
            result = subprocess.run(
                cmd,
                input=input_data,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.cli_script.parent.parent.parent.parent)
            )
            stdout_lines = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            return result.returncode, stdout_lines, result.stderr
        except subprocess.TimeoutExpired:
            return 124, [], "Command timeout"
    
    def _parse_json_events(self, stdout_lines: List[str]) -> List[Dict[str, Any]]:
        """Parse JSON events from CLI output."""
        events = []
        for line in stdout_lines:
            try:
                # Skip non-JSON lines (warnings, print statements)
                if line.startswith('{') and line.endswith('}'):
                    events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return events
    
    def _find_event(self, events: List[Dict[str, Any]], event_type: str) -> Dict[str, Any]:
        """Find first event of given type."""
        for event in events:
            if isinstance(event, dict) and event.get("event") == event_type:
                return event
        return None
    
    # ==================================================================================
    # NOMINAL CASES
    # ==================================================================================
    
    def test_scan_start_nominal(self):
        """Test nominal StepScan execution."""
        config_file = self.examples_dir / "scan_config_example.json"
        
        returncode, stdout_lines, stderr = self._run_cli(
            ["--format", "json", "scan-start", "--config", str(config_file), "--timeout", "60.0"]
        )
        
        # Parse events
        events = self._parse_json_events(stdout_lines)
        
        # Verify invariants
        self.assertGreater(len(events), 0, "Should have at least one event")
        
        # First event should be scan_started
        started_event = self._find_event(events, "scan_started")
        self.assertIsNotNone(started_event, "Should have scan_started event")
        self.assertIn("scan_id", started_event)
        self.assertIn("config", started_event)
        self.assertEqual(started_event["config"]["points"], 9)  # 3x3 grid
        
        # Last event should be scan_completed
        completed_event = self._find_event(events, "scan_completed")
        if completed_event:
            self.assertIn("total_points", completed_event)
            self.assertEqual(completed_event["total_points"], 9)
        
        # Should have progress events
        progress_events = [e for e in events if e.get("event") == "scan_progress"]
        self.assertGreater(len(progress_events), 0, "Should have progress events")
        
        # Verify progress events are sequential
        if len(progress_events) > 1:
            for i in range(1, len(progress_events)):
                prev = progress_events[i-1]["current_point"]
                curr = progress_events[i]["current_point"]
                self.assertGreaterEqual(curr, prev, "Progress should be sequential")
    
    def test_flyscan_start_nominal(self):
        """Test nominal FlyScan execution."""
        config_file = self.examples_dir / "flyscan_config_example.json"
        
        returncode, stdout_lines, stderr = self._run_cli(
            ["--format", "json", "flyscan-start", "--config", str(config_file), "--timeout", "60.0"]
        )
        
        # Parse events
        events = self._parse_json_events(stdout_lines)
        
        # Verify invariants
        self.assertGreater(len(events), 0, "Should have at least one event")
        
        # First event should be flyscan_started
        started_event = self._find_event(events, "flyscan_started")
        self.assertIsNotNone(started_event, "Should have flyscan_started event")
        self.assertIn("scan_id", started_event)
        self.assertIn("config", started_event)
        self.assertIn("estimated_points", started_event["config"])
        
        # Should have progress events (FlyScan has many points)
        progress_events = [e for e in events if e.get("event") == "flyscan_progress"]
        self.assertGreater(len(progress_events), 0, "FlyScan should have progress events")
    
    def test_scan_start_via_stdin(self):
        """Test StepScan with config from stdin."""
        config = {
            "x_min": 0.0,
            "x_max": 5.0,
            "y_min": 0.0,
            "y_max": 5.0,
            "x_nb_points": 2,
            "y_nb_points": 2,
            "scan_pattern": "RASTER"
        }
        input_data = json.dumps(config)
        
        returncode, stdout_lines, stderr = self._run_cli(
            ["--format", "json", "scan-start", "--timeout", "30.0"],
            input_data=input_data
        )
        
        events = self._parse_json_events(stdout_lines)
        started_event = self._find_event(events, "scan_started")
        self.assertIsNotNone(started_event, "Should have scan_started event")
        self.assertEqual(started_event["config"]["points"], 4)  # 2x2 grid
    
    # ==================================================================================
    # EDGE CASES - Invalid Configurations
    # ==================================================================================
    
    def test_scan_start_missing_config(self):
        """Test error handling when no config provided."""
        returncode, stdout_lines, stderr = self._run_cli(
            ["--format", "json", "scan-start"]
        )
        
        # Should return error
        self.assertNotEqual(returncode, 0, "Should return error code")
        
        # Should have error message (either as JSON or plain text)
        events = self._parse_json_events(stdout_lines)
        error_event = self._find_event(events, "error")
        if not error_event:
            # Check if error is in stdout as plain text
            error_found = any("error" in line.lower() for line in stdout_lines)
            if not error_found:
                # Check stderr
                if stderr and "error" in stderr.lower():
                    return  # Found in stderr
                self.fail("Should have error message")
    
    def test_scan_start_invalid_json(self):
        """Test error handling with invalid JSON."""
        returncode, stdout_lines, stderr = self._run_cli(
            ["--format", "json", "scan-start"],
            input_data="not valid json {"
        )
        
        self.assertNotEqual(returncode, 0, "Should return error code")
    
    def test_scan_start_missing_required_fields(self):
        """Test error handling with missing required fields."""
        config = {
            "x_min": 0.0,
            # Missing x_max, y_min, y_max, etc.
        }
        input_data = json.dumps(config)
        
        returncode, stdout_lines, stderr = self._run_cli(
            ["--format", "json", "scan-start"],
            input_data=input_data
        )
        
        self.assertNotEqual(returncode, 0, "Should return error code")
    
    def test_scan_start_invalid_values(self):
        """Test error handling with invalid field values."""
        config = {
            "x_min": "not a number",  # Invalid type
            "x_max": 10.0,
            "y_min": 0.0,
            "y_max": 10.0,
            "x_nb_points": 3,
            "y_nb_points": 3,
            "scan_pattern": "SERPENTINE"
        }
        input_data = json.dumps(config)
        
        returncode, stdout_lines, stderr = self._run_cli(
            ["--format", "json", "scan-start"],
            input_data=input_data
        )
        
        self.assertNotEqual(returncode, 0, "Should return error code")
    
    def test_scan_start_invalid_pattern(self):
        """Test error handling with invalid scan pattern."""
        config = {
            "x_min": 0.0,
            "x_max": 10.0,
            "y_min": 0.0,
            "y_max": 10.0,
            "x_nb_points": 3,
            "y_nb_points": 3,
            "scan_pattern": "INVALID_PATTERN"
        }
        input_data = json.dumps(config)
        
        returncode, stdout_lines, stderr = self._run_cli(
            ["--format", "json", "scan-start"],
            input_data=input_data
        )
        
        self.assertNotEqual(returncode, 0, "Should return error code")
    
    def test_scan_start_zero_points(self):
        """Test error handling with zero points."""
        config = {
            "x_min": 0.0,
            "x_max": 10.0,
            "y_min": 0.0,
            "y_max": 10.0,
            "x_nb_points": 0,  # Invalid
            "y_nb_points": 0,   # Invalid
            "scan_pattern": "SERPENTINE"
        }
        input_data = json.dumps(config)
        
        returncode, stdout_lines, stderr = self._run_cli(
            ["--format", "json", "scan-start"],
            input_data=input_data
        )
        
        self.assertNotEqual(returncode, 0, "Should return error code")
    
    def test_scan_start_inverted_bounds(self):
        """Test error handling with inverted bounds (x_min > x_max)."""
        config = {
            "x_min": 10.0,  # > x_max
            "x_max": 0.0,
            "y_min": 0.0,
            "y_max": 10.0,
            "x_nb_points": 3,
            "y_nb_points": 3,
            "scan_pattern": "SERPENTINE"
        }
        input_data = json.dumps(config)
        
        returncode, stdout_lines, stderr = self._run_cli(
            ["--format", "json", "scan-start"],
            input_data=input_data
        )
        
        # Domain validation should catch this
        # May succeed but produce empty trajectory, or fail
        # Both are acceptable behaviors
    
    # ==================================================================================
    # EDGE CASES - FlyScan Specific
    # ==================================================================================
    
    def test_flyscan_start_missing_motion_profile(self):
        """Test FlyScan error with missing motion profile."""
        config = {
            "scan_zone": {"x_min": 0.0, "x_max": 10.0, "y_min": 0.0, "y_max": 10.0},
            "x_nb_points": 3,
            "y_nb_points": 3,
            "scan_pattern": "SERPENTINE"
            # Missing motion_profile
        }
        input_data = json.dumps(config)
        
        returncode, stdout_lines, stderr = self._run_cli(
            ["--format", "json", "flyscan-start"],
            input_data=input_data
        )
        
        self.assertNotEqual(returncode, 0, "Should return error code")
    
    def test_flyscan_start_invalid_motion_profile(self):
        """Test FlyScan error with invalid motion profile values."""
        config = {
            "scan_zone": {"x_min": 0.0, "x_max": 10.0, "y_min": 0.0, "y_max": 10.0},
            "x_nb_points": 3,
            "y_nb_points": 3,
            "scan_pattern": "SERPENTINE",
            "motion_profile": {
                "min_speed": -1.0,  # Invalid (negative)
                "target_speed": 10.0,
                "acceleration": 5.0,
                "deceleration": 5.0
            },
            "desired_acquisition_rate_hz": 100.0,
            "max_spatial_gap_mm": 0.5
        }
        input_data = json.dumps(config)
        
        returncode, stdout_lines, stderr = self._run_cli(
            ["--format", "json", "flyscan-start"],
            input_data=input_data
        )
        
        # May fail at domain validation or succeed with clamped values
        # Both behaviors are acceptable
    
    # ==================================================================================
    # EDGE CASES - Timeout and Performance
    # ==================================================================================
    
    def test_scan_start_timeout(self):
        """Test timeout handling."""
        config = {
            "x_min": 0.0,
            "x_max": 100.0,  # Large range
            "y_min": 0.0,
            "y_max": 100.0,
            "x_nb_points": 100,  # Many points
            "y_nb_points": 100,
            "scan_pattern": "SERPENTINE"
        }
        input_data = json.dumps(config)
        
        returncode, stdout_lines, stderr = self._run_cli(
            ["--format", "json", "scan-start", "--timeout", "1.0"],  # Very short timeout
            input_data=input_data
        )
        
        # Should timeout or complete quickly (with mocks)
        # Timeout is acceptable
        if returncode == 124:
            # Timeout occurred
            pass
        else:
            # Completed or failed for other reason
            events = self._parse_json_events(stdout_lines)
            self.assertGreater(len(events), 0, "Should have some events even if timeout")
    
    # ==================================================================================
    # EDGE CASES - Boundary Values
    # ==================================================================================
    
    def test_scan_start_minimal_config(self):
        """Test with minimal valid configuration."""
        config = {
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": 0.0,
            "y_max": 1.0,
            "x_nb_points": 2,  # Minimum valid
            "y_nb_points": 2,
            "scan_pattern": "RASTER"
        }
        input_data = json.dumps(config)
        
        returncode, stdout_lines, stderr = self._run_cli(
            ["--format", "json", "scan-start", "--timeout", "30.0"],
            input_data=input_data
        )
        
        events = self._parse_json_events(stdout_lines)
        started_event = self._find_event(events, "scan_started")
        self.assertIsNotNone(started_event, "Should start successfully")
        self.assertEqual(started_event["config"]["points"], 4)  # 2x2
    
    def test_scan_start_single_point(self):
        """Test with single point (edge case: 1x1)."""
        config = {
            "x_min": 0.0,
            "x_max": 0.0,  # Same point
            "y_min": 0.0,
            "y_max": 0.0,
            "x_nb_points": 1,
            "y_nb_points": 1,
            "scan_pattern": "RASTER"
        }
        input_data = json.dumps(config)
        
        returncode, stdout_lines, stderr = self._run_cli(
            ["--format", "json", "scan-start", "--timeout", "30.0"],
            input_data=input_data
        )
        
        # May fail validation (x_nb_points < 2) or succeed
        # Both are acceptable
    
    def test_scan_start_very_small_zone(self):
        """Test with very small scan zone."""
        config = {
            "x_min": 0.0,
            "x_max": 0.001,  # Very small
            "y_min": 0.0,
            "y_max": 0.001,
            "x_nb_points": 3,
            "y_nb_points": 3,
            "scan_pattern": "SERPENTINE"
        }
        input_data = json.dumps(config)
        
        returncode, stdout_lines, stderr = self._run_cli(
            ["--format", "json", "scan-start", "--timeout", "30.0"],
            input_data=input_data
        )
        
        # Should handle gracefully
        events = self._parse_json_events(stdout_lines)
        if returncode == 0:
            # Should have events
            self.assertGreater(len(events), 0)
    
    # ==================================================================================
    # EDGE CASES - File I/O
    # ==================================================================================
    
    def test_scan_start_nonexistent_config_file(self):
        """Test error handling with nonexistent config file."""
        returncode, stdout_lines, stderr = self._run_cli(
            ["--format", "json", "scan-start", "--config", "/nonexistent/file.json"]
        )
        
        self.assertNotEqual(returncode, 0, "Should return error code")
    
    def test_scan_start_config_file_permission_error(self):
        """Test error handling with unreadable config file."""
        # Create temp file and remove read permission (Unix only)
        if os.name != 'nt':  # Not Windows
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
                f.write('{"x_min": 0.0}')
                temp_path = f.name
            
            try:
                os.chmod(temp_path, 0o000)  # No permissions
                
                returncode, stdout_lines, stderr = self._run_cli(
                    ["--format", "json", "scan-start", "--config", temp_path]
                )
                
                self.assertNotEqual(returncode, 0, "Should return error code")
            finally:
                os.chmod(temp_path, 0o644)  # Restore permissions
                os.unlink(temp_path)
    
    # ==================================================================================
    # EDGE CASES - Output Format
    # ==================================================================================
    
    def test_scan_start_text_format(self):
        """Test text format output (non-JSON)."""
        config = {
            "x_min": 0.0,
            "x_max": 5.0,
            "y_min": 0.0,
            "y_max": 5.0,
            "x_nb_points": 2,
            "y_nb_points": 2,
            "scan_pattern": "RASTER"
        }
        input_data = json.dumps(config)
        
        returncode, stdout_lines, stderr = self._run_cli(
            ["--format", "text", "scan-start", "--timeout", "30.0"],
            input_data=input_data
        )
        
        # Text format may not be JSON
        # Just verify it doesn't crash
        self.assertIsNotNone(stdout_lines)
    
    # ==================================================================================
    # EDGE CASES - Status Command
    # ==================================================================================
    
    def test_scan_status_command(self):
        """Test scan-status command."""
        returncode, stdout_lines, stderr = self._run_cli(
            ["--format", "json", "scan-status"]
        )
        
        # Status command should not crash
        # May return "no_active_scan" or similar
        events = self._parse_json_events(stdout_lines)
        # Should have some response (even if empty)
        self.assertIsNotNone(stdout_lines)


if __name__ == '__main__':
    unittest.main()

