"""
Root conftest.py — pytest collection configuration.

Catégorie d'exclusion :
1. TESTS HARDWARE : nécessitent une connexion matérielle physique.
   Exclus de la collection car leurs imports échouent ou ils tentent
   une connexion réelle. À réactiver quand le matériel est branché.
"""

# -- Tests hardware (connexion matérielle physique requise) ----------------------
# Arcus Performax 4EX
_ARCUS_HARDWARE = [
    "src/infrastructure/hardware/arcus_performax_4EX/_tests/adapter_arcus_performax4EX_test.py",
    "src/infrastructure/hardware/arcus_performax_4EX/_tests/arcus_composition_root_sequence_test.py",
    "src/infrastructure/hardware/arcus_performax_4EX/_tests/arcus_hardware_movement_test.py",
    "src/infrastructure/hardware/arcus_performax_4EX/_tests/lifecycle_initialization_test.py",
]
# ADS131A04 ADC
_ADS_HARDWARE = [
    "src/infrastructure/hardware/micro_controller/ads131a04/_tests/adapter_ads131a04_test.py",
    "src/infrastructure/hardware/micro_controller/ads131a04/_tests/acquisition_sequence_test.py",
]

collect_ignore = _ARCUS_HARDWARE + _ADS_HARDWARE


# -- Garde-fou des données du banc (voir src/tool/runtime_data_guard_intention.md) ------------
# Les tests ne doivent ni tourner dans le dossier de l'exécution réelle (branche main), ni
# laisser derrière eux une modification de .aefi_acquisition/ (calibrations, derniers réglages).
import sys
from pathlib import Path

import pytest


def pytest_sessionstart(session):
    from tool import runtime_data_guard as guard

    reason = guard.refusal_reason(Path(session.config.rootpath), guard.default_environ())
    if reason:
        pytest.exit(reason, returncode=4)
    session.config._aefi_runtime_snapshots = [
        snapshot
        for runtime_dir in guard.runtime_dirs(Path(session.config.rootpath), Path.cwd())
        if (snapshot := guard.RuntimeDataSnapshot.take(runtime_dir)) is not None
    ]


def pytest_sessionfinish(session, exitstatus):
    from tool import runtime_data_guard as guard

    for snapshot in getattr(session.config, "_aefi_runtime_snapshots", []):
        changes = snapshot.changes()
        if not changes.any:
            snapshot.discard()
            continue
        snapshot.restore(changes)
        for line in guard.report(changes, snapshot.runtime_dir, snapshot.backup_dir):
            print(line, file=sys.stderr)
