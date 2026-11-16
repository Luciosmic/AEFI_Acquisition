"""Sens des dépendances du module : le domaine et l'application restent purs, et le module ne se mêle pas à `src/`.

`solidai verify` ne voit pas `aefi_acquisition_upstream/` (hors des quatre couches) ni la collision de noms avec
les dossiers `domain`, `application`, `infrastructure` et `interface` de `src/` : ce test lit les imports.
"""

import ast
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parents[1]

# Racines que le domaine et l'application n'importent jamais.
FORBIDDEN_IN_CORE = {"PySide6", "pandas", "h5py", "pathlib", "aefi_acquisition_upstream", "interface", "src"}
# Noms de couches de src/ : un import non qualifié viserait src/ ou le module selon sys.path.
LAYER_NAMES = {"domain", "application", "infrastructure", "interface"}


def _python_files(*layers: str):
    for layer in layers:
        yield from sorted((MODULE_DIR / layer).rglob("*.py"))


def _imports(path: Path):
    """(racine importée, numéro de ligne, import relatif ?) de chaque import du fichier."""
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name.split(".")[0], node.lineno, False
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                yield "", node.lineno, True
            else:
                yield (node.module or "").split(".")[0], node.lineno, False


def test_domain_and_application_import_no_framework_io_or_upstream():
    offenders = []
    for path in _python_files("domain", "application"):
        for root, line, _ in _imports(path):
            if root in FORBIDDEN_IN_CORE:
                offenders.append(f"{path.relative_to(MODULE_DIR)}:{line} importe {root}")
    assert offenders == []


def test_no_module_imports_a_layer_without_qualifying_it():
    offenders = []
    for path in sorted(MODULE_DIR.rglob("*.py")):
        if ".venv" in path.parts or "__pycache__" in path.parts:
            continue
        if "aefi_acquisition_upstream" in path.parts:
            continue  # the one place where `interface` is meant to be src/'s, once sys.path is settled
        for root, line, relative in _imports(path):
            if not relative and root in LAYER_NAMES:
                offenders.append(f"{path.relative_to(MODULE_DIR)}:{line} importe {root} sans le qualifier")
    assert offenders == []


def test_the_scan_sees_the_domain_it_guards():
    assert any(_python_files("domain")), "aucun fichier du domaine : le test ne garde plus rien"


def _imported_names(path: Path):
    """(module importé tel qu'écrit, numéro de ligne), relatifs compris."""
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name, node.lineno
        elif isinstance(node, ast.ImportFrom):
            yield "." * node.level + (node.module or ""), node.lineno


def test_presenters_import_neither_qt_nor_the_domain_nor_the_infrastructure():
    offenders = []
    presenters = sorted(
        path for path in (MODULE_DIR / "interface").glob("*_presenter/*.py") if path.name != "__init__.py"
    )
    for path in presenters:
        for name, line in _imported_names(path):
            parts = name.lstrip(".").split(".")
            if parts[0] in {"PySide6", "pandas", "h5py", "aefi_acquisition_upstream"} or "domain" in parts or "infrastructure" in parts:
                offenders.append(f"{path.relative_to(MODULE_DIR)}:{line} importe {name}")
    assert presenters, "aucun presenter : le test ne garde plus rien"
    assert offenders == []
