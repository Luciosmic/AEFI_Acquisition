"""
Visualization App
Main entry point.
"""

import sys
import logging
import argparse
from pathlib import Path
from PySide6.QtWidgets import QApplication

# visualisation/ -> aefi_post_processor_module/ -> external_modules/ -> repo root
_current = Path(__file__).resolve().parent
_external_modules = _current.parent.parent
project_root = _external_modules.parent
for p in (_external_modules, project_root):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

from aefi_post_processor_module.logging_setup import configure_logging
from aefi_post_processor_module.visualisation.model import VisualisationModel
from aefi_post_processor_module.visualisation.view import VisualisationView
from aefi_post_processor_module.visualisation.presenter import VisualisationPresenter

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="AEFI Data Visualization")
    parser.add_argument(
        "--repo", 
        type=str, 
        default=str(
            project_root
            / "external_modules"
            / "aefi_post_processor_module"
            / "_tests"
            / "synthetic_scans_data_repository"
        ),
        help="Path to HDF5 data repository"
    )
    args = parser.parse_args()
    
    feedback = configure_logging(project_root / ".aefi_acquisition" / "logs" / "post_processor.log")

    repo_path = Path(args.repo)
    if not repo_path.exists():
        logger.warning("visualisation.repo_missing repo=%s", repo_path)
    
    app = QApplication(sys.argv)
    app.setApplicationName("AEFI Visualisation")
    
    model = VisualisationModel(repo_path)
    view = VisualisationView()
    feedback.attach(view.append_feedback)
    presenter = VisualisationPresenter(view, model)
    
    view.show()
    
    logger.info("visualisation.opened repo=%s", repo_path)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
