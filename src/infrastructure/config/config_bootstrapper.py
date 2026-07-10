import shutil
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigBootstrapper:
    """
    Seeds .aefi_acquisition/configs/ from config_templates/ on first run.
    Copies only missing files — never overwrites user-edited values.
    """

    def __init__(self, templates_dir: Path, runtime_dir: Path):
        self._templates_dir = templates_dir
        self._runtime_dir = runtime_dir

    def ensure_configs_exist(self) -> list[str]:
        """
        Copies missing JSON configs from templates to runtime dir.
        Returns filenames that were copied (empty list if all already present).
        """
        self._runtime_dir.mkdir(parents=True, exist_ok=True)

        copied = []
        for template_file in sorted(self._templates_dir.glob("*.json")):
            target = self._runtime_dir / template_file.name
            if not target.exists():
                shutil.copy2(template_file, target)
                copied.append(template_file.name)
                logger.info("Config initialisée depuis template : %s", template_file.name)

        return copied
