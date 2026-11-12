"""
Runtime Data Guard

See runtime_data_guard_intention.md.
"""

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Mapping, Optional

RUNTIME_DIR_NAME = ".aefi_acquisition"
# Heavy and never a setting: not worth copying, not worth restoring.
EXCLUDED_DIRS = frozenset({"logs", "__pycache__"})
PROTECTED_BRANCHES = frozenset({"main"})
OVERRIDE_ENV = "AEFI_ALLOW_TESTS_ON_MAIN"


def current_branch(repo_root: Path) -> Optional[str]:
    """The checked-out branch, or None when git cannot say (not a repository, detached, no git)."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_root, capture_output=True, text=True, timeout=10, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    branch = result.stdout.strip()
    return branch if result.returncode == 0 and branch and branch != "HEAD" else None


def refusal_reason(repo_root: Path, environ: Mapping[str, str]) -> Optional[str]:
    """Why the tests must not run here, or None. The checkout on a protected branch is where the bench
    app really runs: its runtime data (calibrations, last settings) is not reproducible."""
    branch = current_branch(repo_root)
    if branch in PROTECTED_BRANCHES and not environ.get(OVERRIDE_ENV):
        return (
            f"Tests refusés : ce dossier ({repo_root}) est sur la branche « {branch} », celle où l'application "
            f"tourne sur le banc. Les tests peuvent y écraser des réglages et des calibrations qu'aucun git ne "
            f"restitue. Lancez-les dans le worktree de develop (ce sont les mêmes commits), ou posez "
            f"{OVERRIDE_ENV}=1 en connaissance de cause."
        )
    return None


@dataclass
class Changes:
    modified: List[str] = field(default_factory=list)
    deleted: List[str] = field(default_factory=list)
    added: List[str] = field(default_factory=list)

    @property
    def any(self) -> bool:
        return bool(self.modified or self.deleted or self.added)


class RuntimeDataSnapshot:
    """A copy of the runtime data taken before the tests, to compare with after and to restore from."""

    def __init__(self, runtime_dir: Path, backup_dir: Path) -> None:
        self.runtime_dir = runtime_dir
        self.backup_dir = backup_dir

    @classmethod
    def take(cls, runtime_dir: Path) -> Optional["RuntimeDataSnapshot"]:
        if not runtime_dir.is_dir():
            return None
        backup_dir = Path(tempfile.mkdtemp(prefix="aefi_runtime_backup_"))
        shutil.copytree(
            runtime_dir, backup_dir / RUNTIME_DIR_NAME, ignore=shutil.ignore_patterns(*EXCLUDED_DIRS),
            dirs_exist_ok=True,
        )
        return cls(runtime_dir, backup_dir)

    @property
    def _backup_root(self) -> Path:
        return self.backup_dir / RUNTIME_DIR_NAME

    @staticmethod
    def _files(root: Path) -> List[str]:
        found = []
        for path in root.rglob("*"):
            relative = path.relative_to(root)
            if path.is_file() and not EXCLUDED_DIRS.intersection(relative.parts):
                found.append(relative.as_posix())
        return found

    def changes(self) -> Changes:
        before, after = set(self._files(self._backup_root)), set(self._files(self.runtime_dir))
        changes = Changes(deleted=sorted(before - after), added=sorted(after - before))
        for name in sorted(before & after):
            if (self._backup_root / name).read_bytes() != (self.runtime_dir / name).read_bytes():
                changes.modified.append(name)
        return changes

    def restore(self, changes: Changes) -> None:
        """Put back what the tests modified or deleted. Files they added are left alone and only reported."""
        for name in changes.modified + changes.deleted:
            target = self.runtime_dir / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self._backup_root / name, target)

    def discard(self) -> None:
        shutil.rmtree(self.backup_dir, ignore_errors=True)


def runtime_dirs(rootpath: Path, cwd: Path) -> List[Path]:
    """The runtime directories tests can reach: tests open it relative to the working directory."""
    seen, found = set(), []
    for base in (cwd, rootpath):
        candidate = (base / RUNTIME_DIR_NAME).resolve()
        if candidate.is_dir() and candidate not in seen:
            seen.add(candidate)
            found.append(candidate)
    return found


def report(changes: Changes, runtime_dir: Path, backup_dir: Path) -> List[str]:
    lines = [f"GARDE-FOU DONNÉES DU BANC : les tests ont touché {runtime_dir}"]
    for label, names in (("modifiés", changes.modified), ("supprimés", changes.deleted), ("créés", changes.added)):
        if names:
            lines.append(f"  {label} : {', '.join(names)}")
    if changes.modified or changes.deleted:
        lines.append("  -> les fichiers modifiés ou supprimés ont été remis à leur état d'avant les tests.")
        lines.append("    (si l'application tournait en même temps, ses écritures de cette période sont aussi revenues en arrière)")
    lines.append(f"  Copie d'avant les tests conservée dans {backup_dir}")
    lines.append("  Un test qui écrit dans les données du banc est à corriger : il doit viser un dossier temporaire.")
    return lines


def default_environ() -> Mapping[str, str]:
    return os.environ
