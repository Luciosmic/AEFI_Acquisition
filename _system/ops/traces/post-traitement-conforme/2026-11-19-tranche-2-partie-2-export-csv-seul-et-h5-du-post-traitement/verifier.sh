#!/bin/bash
# usage: verifier.sh <etape> ; V1 V2 V3 -> logs dans la trace
cd "/Users/luis/Library/CloudStorage/Dropbox/Luis/1 PROJETS/1 - THESE/EXPERIMENTAL/AEFI_Acquisition_dev_post_processor"
export UV_PROJECT_ENVIRONMENT=~/.venvs/AEFI_Acquisition_dev_post_processor QT_QPA_PLATFORM=offscreen
T=_system/ops/traces/post-traitement-conforme/2026-11-19-tranche-2-partie-2-export-csv-seul-et-h5-du-post-traitement
E=$1
uv run pytest external_modules/aefi_post_processor_module -q > $T/pytest-v1-etape-$E.log 2>&1
~/.venvs/solidai-verify/bin/solidai verify --entry . --target external_modules/aefi_post_processor_module > $T/solidai-verify-v2-etape-$E.log 2>&1
uv run pytest src/infrastructure/aefi_post_processor_port src/application/scan/scan_application_service/_tests/scan_export_with_post_processing_integration_test.py -q > $T/pytest-v3-etape-$E.log 2>&1
echo "V1: $(tail -1 $T/pytest-v1-etape-$E.log)"; grep FAILED $T/pytest-v1-etape-$E.log | sed 's/.*:://'
echo "V2: $(sed -n 3p $T/solidai-verify-v2-etape-$E.log)"; grep -i "error" $T/solidai-verify-v2-etape-$E.log | grep -v "0 error" | head
echo "V3: $(tail -1 $T/pytest-v3-etape-$E.log)"
