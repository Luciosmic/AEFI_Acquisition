# Scan CLI - JSON-First Interface

**Step 8: Interface Layer (The "Headless Controller")**

CLI interface for Scan operations, following the "Strict Domain Verification" cycle pattern.

## Features

- **JSON-First**: All output in JSON format (`--format json`)
- **Atomic Commands**: Each command is self-contained
- **Event-Driven**: Real-time progress via JSON events
- **Tested**: ✅ 20 integration tests + 7 connection tests

## Commands

### StepScan

Start a StepScan (stop-and-acquire at each point):

```bash
python src/interface/cli/scan_cli.py --format json scan-start --config examples/scan_config_example.json
```

Or pipe JSON from stdin:

```bash
echo '{"x_min": 0.0, "x_max": 10.0, "y_min": 0.0, "y_max": 10.0, "x_nb_points": 3, "y_nb_points": 3, "scan_pattern": "SERPENTINE"}' | \
  python src/interface/cli/scan_cli.py --format json scan-start
```

### FlyScan

Start a FlyScan (continuous motion with acquisition):

```bash
python src/interface/cli/scan_cli.py --format json flyscan-start --config examples/flyscan_config_example.json
```

### Status

Get scan status:

```bash
python src/interface/cli/scan_cli.py --format json scan-status
```

## Configuration Format

### StepScan Config

```json
{
  "x_min": 0.0,
  "x_max": 10.0,
  "y_min": 0.0,
  "y_max": 10.0,
  "x_nb_points": 3,
  "y_nb_points": 3,
  "scan_pattern": "SERPENTINE",
  "stabilization_delay_ms": 300,
  "averaging_per_position": 10,
  "uncertainty_volts": 0.001
}
```

### FlyScan Config

```json
{
  "scan_zone": {
    "x_min": 0.0,
    "x_max": 10.0,
    "y_min": 0.0,
    "y_max": 10.0
  },
  "x_nb_points": 3,
  "y_nb_points": 3,
  "scan_pattern": "SERPENTINE",
  "motion_profile": {
    "min_speed": 0.1,
    "target_speed": 10.0,
    "acceleration": 5.0,
    "deceleration": 5.0
  },
  "desired_acquisition_rate_hz": 100.0,
  "max_spatial_gap_mm": 0.5,
  "acquisition_rate_hz": 100.0
}
```

## Output Format

All events are output as JSON objects, one per line:

```json
{
  "event": "scan_started",
  "scan_id": "uuid",
  "config": {...},
  "timestamp": "2025-12-18T05:58:54.814603"
}
```

```json
{
  "event": "scan_progress",
  "current_point": 1,
  "total_points": 9,
  "progress_percent": 11.11,
  "point_data": {...},
  "timestamp": "2025-12-18T05:58:55.123456"
}
```

```json
{
  "event": "scan_completed",
  "scan_id": "uuid",
  "total_points": 9,
  "timestamp": "2025-12-18T05:59:00.789012"
}
```

## Integration with Cycle

This CLI implements **Step 8** of the "Strict Domain Verification" cycle:

1. ✅ Requirement Gathering
2. ✅ Inspiration Analysis
3. ✅ Architecture Review
4. ✅ Pure Domain Modeling
5. ✅ Anti-Corruption Layer
6. ✅ Domain Service Composition
7. ✅ Application Layer Orchestration
8. ✅ **Interface Layer (This CLI)**
9. ✅ **Deterministic Integration Verification** (See `tests/` directory)

## Testing

**Step 9** (Deterministic Integration Verification) is implemented in `tests/`:

- **20 integration tests** covering nominal cases and edge cases
- **7 connection tests** validating CLI ↔ UI connection
- **Subprocess-based testing** (CLI called as external process)
- **JSON parsing and validation** of output
- **Invariant verification** (event sequence, progress monotonicity, etc.)

See `tests/README.md` for detailed test documentation.

### Quick Test Run

```bash
# All CLI tests
python -m pytest src/interface/cli/tests/ -v

# Connection tests (CLI ↔ UI)
python -m pytest src/interface/cli/tests/test_ui_connection.py -v

# Integration tests (edge cases)
python -m pytest src/interface/cli/tests/test_scan_cli_integration.py -v
```

### Test Coverage

- ✅ Nominal cases (3 tests)
- ✅ Invalid configurations (7 tests)
- ✅ FlyScan-specific (2 tests)
- ✅ Boundary values (3 tests)
- ✅ Timeout handling (1 test)
- ✅ File I/O errors (2 tests)
- ✅ Output format (1 test)
- ✅ Status command (1 test)
- ✅ **UI connection validation (7 tests)**

See `tests/EDGE_CASES.md` for detailed edge case documentation.

## Connection to UI

**✅ Validated**: The CLI (tested controller) is connected to the UI via the presenter.

- **Same Service**: Both use `ScanApplicationService`
- **Same Interface**: Both implement `IScanOutputPort`
- **Same Pattern**: `set_output_port()` used in both cases
- **Connected Signals**: Panels ↔ Presenter ↔ Service

See `CONNECTION_UI.md` and `VALIDATION.md` for detailed connection documentation.

## Architecture

```
CLI (Tested)          UI (PySide6)
    │                      │
    │                      │
    └──────────┬───────────┘
               │
    ScanApplicationService
               │
        (Domain Logic)
```

Both interfaces use the same service, so **CLI tests validate UI behavior**.
