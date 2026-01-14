# CLI Integration Tests

**Step 9: Deterministic Integration Verification**

## Purpose

These tests verify the CLI interface by:
1. Calling CLI via subprocess
2. Parsing JSON output
3. Verifying invariants
4. Testing edge cases

## Test Structure

### Test File
- `test_scan_cli_integration.py`: Main test suite

### Documentation
- `TEST_RESULTS.md`: Test execution results and summary
- `EDGE_CASES.md`: Detailed edge case documentation
- `README.md`: This file

## Running Tests

### All Tests
```bash
python -m pytest src/interface/cli/tests/test_scan_cli_integration.py -v
```

### Specific Test
```bash
python -m pytest src/interface/cli/tests/test_scan_cli_integration.py::TestScanCLIIntegration::test_scan_start_nominal -v
```

### With Coverage
```bash
python -m pytest src/interface/cli/tests/test_scan_cli_integration.py --cov=src/interface/cli --cov-report=html
```

## Test Categories

### 1. Nominal Cases (3 tests)
- Valid StepScan execution
- Valid FlyScan execution
- Config from stdin

### 2. Invalid Configurations (7 tests)
- Missing config
- Invalid JSON
- Missing fields
- Invalid values
- Invalid pattern
- Zero points
- Inverted bounds

### 3. FlyScan-Specific (2 tests)
- Missing motion profile
- Invalid motion profile

### 4. Boundary Values (3 tests)
- Minimal config
- Single point
- Very small zone

### 5. Timeout (1 test)
- Timeout handling

### 6. File I/O (2 tests)
- Nonexistent file
- Permission error

### 7. Output Format (1 test)
- Text format

### 8. Status Command (1 test)
- Status query

**Total: 20 tests**

## Expected Behaviors

### Success
- Return code: 0
- JSON events in sequence
- Valid JSON format
- Required fields present

### Failure
- Return code: != 0
- Error message in JSON or stderr
- Graceful error handling

## Invariants

1. Event sequence: `started` → `progress*` → `completed`/`failed`/`cancelled`
2. Progress monotonicity: `current_point` non-decreasing
3. JSON validity: All events valid JSON
4. Required fields: `event`, `timestamp` present
5. Point count: Matches configuration

## Notes

- Tests use mock adapters (no real hardware)
- Some edge cases have multiple acceptable behaviors
- Focus on CLI interface, not domain logic
- Timeouts set for mock execution speed

