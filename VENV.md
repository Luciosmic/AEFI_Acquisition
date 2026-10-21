# Environnement Python — local à chaque machine, jamais dans Dropbox

Ce dossier est synchronisé par Dropbox. Un venv est propre à une machine (chemins absolus, binaires) : il ne doit pas vivre ici. Chaque machine crée le sien dans `~/.venvs/AEFI_Acquisition`, à partir de `pyproject.toml` et `uv.lock`, qui eux restent versionnés. uv mutualise les paquets dans son cache : rien n'est dupliqué.

## Créer le venv (une fois par machine)

Depuis la racine du dossier :

```bash
export UV_PROJECT_ENVIRONMENT=~/.venvs/AEFI_Acquisition
uv sync --extra dev
~/.venvs/AEFI_Acquisition/bin/python -c "import numpy, PySide6"   # vérification
```

## Lancer l'application

```bash
launch/launch.sh
```

`launch/launch.sh` exporte lui-même `UV_PROJECT_ENVIRONMENT` avant `uv run`.

## À ne pas faire

Ne pas lancer `uv sync` ou `uv run` sans `UV_PROJECT_ENVIRONMENT` : uv recréerait `.venv/` ici, dans Dropbox.
