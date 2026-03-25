"""
Visualization App
Main entry point.
"""

import sys
import argparse
from pathlib import Path
from PySide6.QtWidgets import QApplication

_current = Path(__file__).resolve().parent
_external_modules = _current.parent.parent
project_root = _external_modules.parent
for p in (_external_modules, project_root):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

from post_processor_module.visualisation.model import VisualisationModel
from post_processor_module.visualisation.view import VisualisationView
from post_processor_module.visualisation.presenter import VisualisationPresenter

def main():
    parser = argparse.ArgumentParser(description="AEFI Data Visualization")
    parser.add_argument(
        "--repo", 
        type=str, 
        default=str(
            project_root
            / "external_modules"
            / "post_processor_module"
            / "_tests"
            / "synthetic_scans_data_repository"
        ),
        help="Path to HDF5 data repository"
    )
    args = parser.parse_args()
    
    repo_path = Path(args.repo)
    if not repo_path.exists():
        print(f"Warning: Repository path does not exist: {repo_path}")
        # Try to fallback to the gitignore whitelisted one if default fails?
        # But for now, we point to the synthetic one we just made.
    
    app = QApplication(sys.argv)
    app.setApplicationName("AEFI Visualisation")
    
    model = VisualisationModel(repo_path)
    view = VisualisationView()
    presenter = VisualisationPresenter(view, model)
    
    view.show()
    
    print(f"Started Visualization App. Repo: {repo_path}")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
