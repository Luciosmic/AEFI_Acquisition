"""
Real Operator Repository — the operators registry as a JSON file
(see real_operator_repository_intention.md).
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from domain.operator_registry.entities.operator.operator import Operator
from domain.operator_registry.repositories.i_operator_repository import IOperatorRepository
from domain.shared_kernel.operation_result import OperationResult

logger = logging.getLogger(__name__)


class RealOperatorRepository(IOperatorRepository):
    DEFAULT_PATH = Path(".aefi_acquisition/operators/operators.json")

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        self._path = storage_path or self.DEFAULT_PATH

    def find_all(self) -> OperationResult[List[Operator], str]:
        loaded = self._load()
        if loaded.is_failure:
            return OperationResult.fail(loaded.error)
        try:
            operators = [self._deserialize(raw) for raw in loaded.value]
        except (KeyError, TypeError, ValueError) as error:
            logger.error("Operator registry %s: malformed entry: %s", self._path, error)
            return OperationResult.fail(f"registre des opérateurs mal formé ({self._path}) : {error}")
        return OperationResult.ok(operators)

    def add(self, operator: Operator) -> OperationResult[None, str]:
        loaded = self._load()
        if loaded.is_failure:  # never overwrite a registry we could not read
            return OperationResult.fail(loaded.error)
        temporary = self._path.with_suffix(".json.tmp")
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with open(temporary, "w", encoding="utf-8") as f:
                json.dump({"operators": loaded.value + [self._serialize(operator)]}, f, indent=2, ensure_ascii=False)
            os.replace(temporary, self._path)
        except OSError as error:
            logger.error("Operator registry %s: cannot write: %s", self._path, error)
            return OperationResult.fail(f"registre des opérateurs non écrit ({self._path}) : {error}")
        logger.info("Operator registry: operator_id=%s name=%s saved to %s", operator.operator_id, operator.name, self._path)
        return OperationResult.ok(None)

    def _load(self) -> OperationResult[List[Dict[str, Any]], str]:
        if not self._path.exists():
            return OperationResult.ok([])
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                return OperationResult.ok(list(json.load(f)["operators"]))
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
            logger.error("Operator registry %s: unreadable: %s", self._path, error)
            return OperationResult.fail(f"registre des opérateurs illisible ({self._path}) : {error}")

    @staticmethod
    def _serialize(operator: Operator) -> Dict[str, Any]:
        return {
            "operator_id": str(operator.operator_id),
            "name": operator.name,
            "registered_at": operator.registered_at.isoformat(),
        }

    @staticmethod
    def _deserialize(raw: Dict[str, Any]) -> Operator:
        return Operator(
            operator_id=UUID(raw["operator_id"]),
            name=str(raw["name"]),
            registered_at=datetime.fromisoformat(raw["registered_at"]),
        )
