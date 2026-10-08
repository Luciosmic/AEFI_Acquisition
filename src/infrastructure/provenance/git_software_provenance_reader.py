"""
Git Software Provenance Reader

See git_software_provenance_reader_intention.md.
"""

import logging
import subprocess
from pathlib import Path
from typing import Callable, List, Optional, Sequence

from application.shared.acquisition_parameters.acquisition_conditions_dtos import (
    SoftwareProvenanceDTO,
)
from application.shared.acquisition_parameters.i_software_provenance_port import (
    ISoftwareProvenancePort,
)

logger = logging.getLogger(__name__)

SOFTWARE_NAME = "AEFI Acquisition"
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]  # src/infrastructure/provenance/ -> repo root
GIT_TIMEOUT_S = 5.0

# Runs `git <args>` in the repository; returns stdout, raises on any failure.
GitRunner = Callable[[Sequence[str]], str]


def _run_git(args: Sequence[str], root: Path = REPOSITORY_ROOT) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, timeout=GIT_TIMEOUT_S, check=True
    )
    return completed.stdout.strip()


def _read_version(root: Path = REPOSITORY_ROOT) -> Optional[str]:
    try:
        import tomllib

        with open(root / "pyproject.toml", "rb") as f:
            return tomllib.load(f).get("project", {}).get("version")
    except (ImportError, OSError, ValueError):
        return None


class GitSoftwareProvenanceReader(ISoftwareProvenancePort):
    """Commit, branch and dirty flag from git; version from pyproject.toml."""

    def __init__(
        self,
        run_git: GitRunner = _run_git,
        read_version: Callable[[], Optional[str]] = _read_version,
    ) -> None:
        self._run_git = run_git
        self._read_version = read_version

    def read(self) -> SoftwareProvenanceDTO:
        version = self._read_version()
        problems: List[str] = []
        commit = self._git(["rev-parse", "HEAD"], problems)
        branch = self._git(["rev-parse", "--abbrev-ref", "HEAD"], problems)
        status = self._git(["status", "--porcelain"], problems)
        dirty = None if status is None else bool(status)
        provenance = SoftwareProvenanceDTO(
            name=SOFTWARE_NAME,
            version=version,
            commit=commit,
            branch=branch,
            dirty=dirty,
            unknown_reason="; ".join(problems) or None,
        )
        logger.info(
            "GitSoftwareProvenanceReader: commit=%s branch=%s dirty=%s version=%s",
            commit, branch, dirty, version,
        )
        return provenance

    def _git(self, args: List[str], problems: List[str]) -> Optional[str]:
        try:
            return self._run_git(args)
        except (OSError, subprocess.SubprocessError) as error:
            problems.append(f"git {' '.join(args)} : {type(error).__name__}")
            logger.warning("GitSoftwareProvenanceReader: git %s failed: %s", " ".join(args), error)
            return None
