"""
Real MeasuredObject Repository — the measured_objects registry as a JSON file
(see real_measured_object_repository_intention.md).
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from domain.measured_object_registry.entities.measured_object.measured_object import MeasuredObject
from domain.measured_object_registry.repositories.i_measured_object_repository import IMeasuredObjectRepository
from domain.shared_kernel.operation_result import OperationResult

logger = logging.getLogger(__name__)


class RealMeasuredObjectRepository(IMeasuredObjectRepository):
    DEFAULT_PATH = Path(".aefi_acquisition/measured_objects/measured_objects.json")

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        self._path = storage_path or self.DEFAULT_PATH

    def find_all(self) -> OperationResult[List[MeasuredObject], str]:
        loaded = self._load()
        if loaded.is_failure:
            return OperationResult.fail(loaded.error)
        try:
            measured_objects = [self._deserialize(raw) for raw in loaded.value]
        except (KeyError, TypeError, ValueError) as error:
            logger.error("MeasuredObject registry %s: malformed entry: %s", self._path, error)
            return OperationResult.fail(f"registre des objets mesurés mal formé ({self._path}) : {error}")
        return OperationResult.ok(measured_objects)

    def add(self, measured_object: MeasuredObject) -> OperationResult[None, str]:
        loaded = self._load()
        if loaded.is_failure:  # never overwrite a registry we could not read
            return OperationResult.fail(loaded.error)
        temporary = self._path.with_suffix(".json.tmp")
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with open(temporary, "w", encoding="utf-8") as f:
                json.dump({"measured_objects": loaded.value + [self._serialize(measured_object)]}, f, indent=2, ensure_ascii=False)
            os.replace(temporary, self._path)
        except OSError as error:
            logger.error("MeasuredObject registry %s: cannot write: %s", self._path, error)
            return OperationResult.fail(f"registre des objets mesurés non écrit ({self._path}) : {error}")
        logger.info("MeasuredObject registry: measured_object_id=%s name=%s saved to %s", measured_object.measured_object_id, measured_object.name, self._path)
        return OperationResult.ok(None)

    def _load(self) -> OperationResult[List[Dict[str, Any]], str]:
        if not self._path.exists():
            return OperationResult.ok([])
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                return OperationResult.ok(list(json.load(f)["measured_objects"]))
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
            logger.error("MeasuredObject registry %s: unreadable: %s", self._path, error)
            return OperationResult.fail(f"registre des objets mesurés illisible ({self._path}) : {error}")

    @staticmethod
    def _serialize(measured_object: MeasuredObject) -> Dict[str, Any]:
        return {
            "measured_object_id": str(measured_object.measured_object_id),
            "name": measured_object.name,
            "registered_at": measured_object.registered_at.isoformat(),
        }

    @staticmethod
    def _deserialize(raw: Dict[str, Any]) -> MeasuredObject:
        return MeasuredObject(
            measured_object_id=UUID(raw["measured_object_id"]),
            name=str(raw["name"]),
            registered_at=datetime.fromisoformat(raw["registered_at"]),
        )
