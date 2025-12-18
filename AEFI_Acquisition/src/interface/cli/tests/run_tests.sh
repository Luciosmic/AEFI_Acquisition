#!/bin/bash
# Test runner for CLI integration tests

echo "=== CLI Integration Tests ==="
echo ""

cd "$(dirname "$0")/../../.."

# Run tests
python -m pytest src/interface/cli/tests/test_scan_cli_integration.py -v --tb=short

echo ""
echo "=== Test Summary ==="

