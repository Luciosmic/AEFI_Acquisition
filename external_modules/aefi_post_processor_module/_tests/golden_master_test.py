"""Étalon de non-régression du traitement : mêmes étapes, mêmes métadonnées, à l'identique.

Rejoue `ProcessingPipeline` (nom public, celui que patche l'adaptateur de `src/`) sur trois scans et
compare chaque étape (`np.array_equal`, NaN égaux) et chaque métadonnée à `_tests/golden/<scan>.npz`
et `<scan>.json`. Les étapes sont relues directement dans le `.h5` produit, avec h5py, sans passer
par `DataHandler`, pour que le test survive à son remplacement.

Régénérer l'étalon (seulement après un changement de chiffres voulu et validé) :
    cd external_modules && uv run python -m aefi_post_processor_module._tests.golden_master_test --regenerate
"""

import json
import sys
from pathlib import Path

import h5py
import numpy as np
import pytest

from aefi_post_processor_module.processing.processing_pipeline import ProcessingPipeline

_TESTS = Path(__file__).resolve().parent
_GOLDEN = _TESTS / "golden"
_BATCH = _TESTS / "synthetic_scans_data_repository" / "batch_20260123_201635"

STEPS = ("preprocessed", "phase_calibrated", "amplitude_subtracted", "rotated_frame", "interpolated")

# nom de l'étalon -> (CSV d'entrée, angles de rotation en degrés)
SCANS = {
    "scan_001_baseline": (_BATCH / "scan_001_baseline.csv", (10.0, -20.0, 30.0)),
    "scan_004_rotation_z45": (_BATCH / "scan_004_rotation_z45.csv", (0.0, 0.0, 45.0)),
    "scan_008_incomplete_nan": (_GOLDEN / "scan_008_incomplete_nan.csv", (10.0, -20.0, 30.0)),
}

# Le timestamp d'écriture change à chaque exécution : seul champ exclu de la comparaison.
_VOLATILE_ATTRS = {"timestamp"}


def _plain(value):
    """Valeur d'attribut h5py -> structure JSON (listes, nombres, textes)."""
    if isinstance(value, np.ndarray):
        return _plain(value.tolist())
    if isinstance(value, np.generic):
        return _plain(value.item())
    if isinstance(value, bytes):
        return value.decode("utf-8")
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value


def run_scan(name: str, workdir: Path) -> tuple[dict[str, np.ndarray], dict]:
    """Rejoue le traitement d'un scan ; rend les cinq étapes et leurs métadonnées."""
    csv_path, rotation_angles = SCANS[name]
    output = workdir / f"{name}.h5"
    pipeline = ProcessingPipeline(output)
    summary = pipeline.run_full_pipeline(csv_path, rotation_angles=rotation_angles, reference_point=(0, 0))
    pipeline.data_handler.close()

    arrays: dict[str, np.ndarray] = {}
    metadata: dict[str, dict] = {}
    with h5py.File(output, "r") as h5:
        history = [entry.decode() if isinstance(entry, bytes) else entry for entry in h5.attrs["processing_history"]]
        for step in STEPS:
            group = h5[step]
            arrays[step] = np.array(group["data"])
            metadata[step] = {k: _plain(v) for k, v in group.attrs.items() if k not in _VOLATILE_ATTRS}
    meta = {
        "rotation_angles": list(rotation_angles),
        "reference_point": [0, 0],
        "steps_completed": summary["steps_completed"],
        "history_steps": [entry.split(" @ ")[0] for entry in history],
        "metadata": metadata,
    }
    return arrays, meta


def _same(expected, actual) -> bool:
    """Égalité exacte, NaN égaux, récursive sur listes et dictionnaires."""
    if isinstance(expected, dict):
        return isinstance(actual, dict) and expected.keys() == actual.keys() and all(
            _same(expected[k], actual[k]) for k in expected
        )
    if isinstance(expected, list):
        return isinstance(actual, list) and len(expected) == len(actual) and all(
            _same(e, a) for e, a in zip(expected, actual)
        )
    if isinstance(expected, float) and isinstance(actual, float) and expected != expected:
        return actual != actual
    return expected == actual


@pytest.mark.parametrize("name", sorted(SCANS))
def test_pipeline_reproduces_golden_master(name, tmp_path):
    arrays, meta = run_scan(name, tmp_path)
    golden_arrays = np.load(_GOLDEN / f"{name}.npz")
    golden_meta = json.loads((_GOLDEN / f"{name}.json").read_text(encoding="utf-8"))

    for step in STEPS:
        assert np.array_equal(golden_arrays[step], arrays[step], equal_nan=True), f"{name}: étape {step} différente"
    assert _same(golden_meta, meta), f"{name}: métadonnées différentes"


def regenerate() -> None:
    import tempfile

    for name in SCANS:
        with tempfile.TemporaryDirectory() as tmp:
            arrays, meta = run_scan(name, Path(tmp))
        np.savez_compressed(_GOLDEN / f"{name}.npz", **arrays)
        (_GOLDEN / f"{name}.json").write_text(
            json.dumps(meta, indent=1, sort_keys=True, allow_nan=True) + "\n", encoding="utf-8"
        )
        print(f"étalon écrit : {name}")


if __name__ == "__main__":
    if "--regenerate" in sys.argv:
        regenerate()
