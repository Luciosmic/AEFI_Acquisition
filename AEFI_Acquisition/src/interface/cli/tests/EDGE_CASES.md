# Edge Cases Documentation

## Overview

This document describes all edge cases tested for the Scan CLI, including expected behaviors and failure modes.

## Category 1: Invalid Input Configurations

### 1.1 Missing Configuration
**Test**: `test_scan_start_missing_config`  
**Input**: No config file or stdin  
**Expected**: 
- Return code: 1
- Error message: `{"error": "No config provided..."}`

### 1.2 Invalid JSON Syntax
**Test**: `test_scan_start_invalid_json`  
**Input**: `"not valid json {"`  
**Expected**:
- Return code: 1
- JSON parsing error

### 1.3 Missing Required Fields
**Test**: `test_scan_start_missing_required_fields`  
**Input**: `{"x_min": 0.0}` (missing x_max, y_min, y_max, etc.)  
**Expected**:
- Return code: 1
- KeyError or ValueError for missing fields

### 1.4 Invalid Field Types
**Test**: `test_scan_start_invalid_values`  
**Input**: `{"x_min": "not a number", ...}`  
**Expected**:
- Return code: 1
- TypeError when converting to float

### 1.5 Invalid Scan Pattern
**Test**: `test_scan_start_invalid_pattern`  
**Input**: `{"scan_pattern": "INVALID_PATTERN"}`  
**Expected**:
- Return code: 1
- KeyError when accessing `ScanPattern[INVALID_PATTERN]`

### 1.6 Zero Points
**Test**: `test_scan_start_zero_points`  
**Input**: `{"x_nb_points": 0, "y_nb_points": 0}`  
**Expected**:
- Return code: 1
- Domain validation error: "x_nb_points must be at least 2"

### 1.7 Inverted Bounds
**Test**: `test_scan_start_inverted_bounds`  
**Input**: `{"x_min": 10.0, "x_max": 0.0}`  
**Expected**:
- May succeed but produce empty trajectory
- Or fail at domain validation
- Both behaviors acceptable

## Category 2: FlyScan-Specific Edge Cases

### 2.1 Missing Motion Profile
**Test**: `test_flyscan_start_missing_motion_profile`  
**Input**: Config without `motion_profile` field  
**Expected**:
- Return code: 1
- KeyError when accessing `config_data["motion_profile"]`

### 2.2 Invalid Motion Profile Values
**Test**: `test_flyscan_start_invalid_motion_profile`  
**Input**: `{"motion_profile": {"min_speed": -1.0, ...}}`  
**Expected**:
- May fail at domain validation
- Or succeed with clamped/validated values
- Both behaviors acceptable

## Category 3: Boundary Values

### 3.1 Minimal Valid Configuration
**Test**: `test_scan_start_minimal_config`  
**Input**: 2x2 grid (minimum valid)  
**Expected**:
- Return code: 0
- 4 points acquired
- Events: `scan_started` → `scan_progress` (4x) → `scan_completed`

### 3.2 Single Point
**Test**: `test_scan_start_single_point`  
**Input**: 1x1 grid  
**Expected**:
- Return code: 1 (domain validation: "x_nb_points must be at least 2")
- Or succeed with 1 point (if validation allows)

### 3.3 Very Small Zone
**Test**: `test_scan_start_very_small_zone`  
**Input**: Zone 0.001mm x 0.001mm  
**Expected**:
- Return code: 0
- Should handle gracefully
- May have precision issues but should not crash

## Category 4: Timeout and Performance

### 4.1 Timeout Handling
**Test**: `test_scan_start_timeout`  
**Input**: Large scan (100x100 points) with 1s timeout  
**Expected**:
- Return code: 124 (timeout) or 0 (completed quickly with mocks)
- Partial events may be present

## Category 5: File I/O Edge Cases

### 5.1 Nonexistent File
**Test**: `test_scan_start_nonexistent_config_file`  
**Input**: `--config /nonexistent/file.json`  
**Expected**:
- Return code: 1
- FileNotFoundError

### 5.2 Permission Error
**Test**: `test_scan_start_config_file_permission_error`  
**Input**: File with no read permissions (Unix only)  
**Expected**:
- Return code: 1
- PermissionError

## Category 6: Output Format

### 6.1 Text Format
**Test**: `test_scan_start_text_format`  
**Input**: `--format text`  
**Expected**:
- Return code: 0
- Output may not be JSON (human-readable)
- Should not crash

## Category 7: Status Command

### 7.1 Status Query
**Test**: `test_scan_status_command`  
**Input**: `scan-status`  
**Expected**:
- Return code: 0
- Response: `{"status": "no_active_scan", ...}`
- Should not crash

## Category 8: Stdin Input

### 8.1 Config from Stdin
**Test**: `test_scan_start_via_stdin`  
**Input**: JSON piped to stdin  
**Expected**:
- Return code: 0
- Should work identically to `--config` file
- Events: `scan_started` → `scan_progress` → `scan_completed`

## Invariants to Verify

For all successful scans:

1. **Event Sequence**: Must start with `scan_started` or `flyscan_started`
2. **Progress Monotonicity**: `current_point` in progress events must be non-decreasing
3. **Completion**: Must end with `scan_completed`, `scan_failed`, or `scan_cancelled`
4. **JSON Validity**: All events must be valid JSON
5. **Required Fields**: Events must have `event` and `timestamp` fields
6. **Point Count**: `total_points` in completion event should match grid size (StepScan) or estimated (FlyScan)

## Error Response Format

All errors should be in JSON format:

```json
{
  "error": "Error message description"
}
```

Or in stderr for non-JSON errors (file I/O, etc.).

## Test Execution Notes

- Tests use mock adapters (no real hardware)
- Timeouts are set appropriately for mock execution
- Some edge cases may have multiple acceptable behaviors
- Focus on verifying CLI interface, not domain logic (domain has its own tests)

