"""
Real Hardware Component Repository

Responsibility:
- Implement `IHardwareComponentRepository` with one plain JSON file per
  component kind: `.aefi_acquisition/calibrations/hardware_components/<kind>.json`,
  shaped `{"entries": [...], "selections": [...]}`, both lists append-only.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import NAMESPACE_URL, UUID, uuid5

from domain.calibration.entities.hardware_component_characterization_entry.hardware_component_characterization_entry import (
    HardwareComponentCharacterizationEntry,
)
from domain.calibration.entities.hardware_component_selection.hardware_component_selection import (
    HardwareComponentSelection,
)
from domain.calibration.repositories.i_hardware_component_repository import IHardwareComponentRepository
from domain.calibration.value_objects.component_characterization.component_characterization import (
    ComponentCharacterization,
)
from domain.calibration.value_objects.hardware_component_kind.hardware_component_kind import (
    HardwareComponentKind,
)

logger = logging.getLogger(__name__)

# Files written before the registries moved to hardware_components/ (2026-09-25),
# relative to the calibrations directory: read until the first write migrates them.
# (No legacy file for the sensor: sensor_calibration.json is the angle registry.)
_LEGACY_FILE_NAMES = {
    HardwareComponentKind.CONDITIONING_ELECTRONICS_BOARD: ("conditioning_electronics_board_calibration.json",),
    HardwareComponentKind.EXCITATION_ELECTRONICS_BOARD: (
        "excitation_electronics_board_calibration.json",
        "excitation_electronic_board_calibration.json",
    ),
    HardwareComponentKind.SIGNAL_GENERATION_CHIP: ("signal_generation_chip_calibration.json",),
    HardwareComponentKind.ADC: ("adc_calibration.json",),
    HardwareComponentKind.MICROCONTROLLER: ("microcontroller_calibration.json",),
    HardwareComponentKind.MOTORS: ("motors_calibration.json",),
}
# Entries written before components had their own name were tagged by a full
# HardwareSignature; the component name was this field of it.
_LEGACY_SIGNATURE_FIELDS = {
    HardwareComponentKind.CONDITIONING_ELECTRONICS_BOARD: "conditioning_board_version",
    HardwareComponentKind.EXCITATION_ELECTRONICS_BOARD: "excitation_board_version",
}


class RealHardwareComponentRepository(IHardwareComponentRepository):
    """JSON-file-backed component catalog + mounting log, one file per kind."""

    DEFAULT_DIR = Path(".aefi_acquisition/calibrations")  # files live in DEFAULT_DIR / "hardware_components"

    def __init__(self, storage_dir: Optional[Path] = None):
        self._storage_dir = storage_dir or self.DEFAULT_DIR

    # -- catalog ------------------------------------------------------------------

    def add(self, entry: HardwareComponentCharacterizationEntry) -> None:
        data = self._load(entry.kind)
        data["entries"].append(
            {
                "entry_id": str(entry.entry_id),
                "component_name": entry.component_name,
                "characterization": {
                    key: list(map(list, value)) if isinstance(value, tuple) else value
                    for key, value in entry.characterization.values.items()
                },
                "recorded_at": entry.recorded_at.isoformat(),
            }
        )
        self._write(entry.kind, data)
        logger.info(
            "Saved %s characterization entry %s for '%s'", entry.kind.value, entry.entry_id, entry.component_name
        )

    def find_all(self, kind: HardwareComponentKind) -> List[HardwareComponentCharacterizationEntry]:
        return [self._deserialize_entry(kind, raw) for raw in self._load(kind)["entries"]]

    # -- mounting log -------------------------------------------------------------

    def add_selection(self, selection: HardwareComponentSelection) -> None:
        data = self._load(selection.kind)
        data["selections"].append(
            {
                "mounting_id": str(selection.mounting_id),
                "component_name": selection.component_name,
                "selected_at": selection.selected_at.isoformat(),
            }
        )
        self._write(selection.kind, data)
        logger.info("Saved %s mounting of '%s'", selection.kind.value, selection.component_name)

    def find_selections(self, kind: HardwareComponentKind) -> List[HardwareComponentSelection]:
        selections = []
        for raw in self._load(kind)["selections"]:
            name = raw.get("component_name") or raw["board_name"]
            mounting_id = raw.get("mounting_id")
            selections.append(
                HardwareComponentSelection(
                    kind=kind,
                    component_name=name,
                    selected_at=datetime.fromisoformat(raw["selected_at"]),
                    # mountings recorded before they had an identity: a stable one derived from the record
                    mounting_id=UUID(mounting_id)
                    if mounting_id
                    else uuid5(NAMESPACE_URL, f"{kind.value}:{name}:{raw['selected_at']}"),
                )
            )
        return selections

    # -- file mechanics -----------------------------------------------------------

    def _path(self, kind: HardwareComponentKind) -> Path:
        return self._storage_dir / "hardware_components" / f"{kind.value}.json"

    def _load(self, kind: HardwareComponentKind) -> Dict[str, Any]:
        path = self._path(kind)
        if not path.exists():
            for legacy in _LEGACY_FILE_NAMES.get(kind, ()):
                if (self._storage_dir / legacy).exists():
                    path = self._storage_dir / legacy
                    break
        if not path.exists():
            return {"entries": [], "selections": []}
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("Failed to load hardware component registry %s: %s", path, exc)
            return {"entries": [], "selections": []}
        data.setdefault("entries", [])
        data.setdefault("selections", [])
        return data

    def _write(self, kind: HardwareComponentKind, data: Dict[str, Any]) -> None:
        path = self._path(kind)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def _deserialize_entry(kind: HardwareComponentKind, raw: Dict[str, Any]) -> HardwareComponentCharacterizationEntry:
        name = raw.get("component_name") or raw.get("board_name")
        if not name:
            name = raw["hardware_signature"][_LEGACY_SIGNATURE_FIELDS[kind]]
        values = raw.get("characterization", raw.get("response", {}))
        known = {q.key for q in kind.quantities}
        dropped = set(values) - known
        if dropped:
            logger.warning("%s '%s': ignoring quantities no longer declared %s", kind.value, name, sorted(dropped))
        return HardwareComponentCharacterizationEntry(
            entry_id=UUID(raw["entry_id"]),
            component_name=name,
            characterization=ComponentCharacterization.of(kind, {k: v for k, v in values.items() if k in known}),
            recorded_at=datetime.fromisoformat(raw["recorded_at"]),
        )
