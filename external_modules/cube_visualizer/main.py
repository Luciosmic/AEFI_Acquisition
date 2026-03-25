"""
Shim entry point — delegates to interface/main.py (DDD refactoring).

This file is kept for backwards compatibility with external launchers.
The real implementation now lives in the DDD layers:
  domain/ application/ infrastructure/ interface/
"""
import sys
import os

# Allow running this file directly: add the parent of cube_visualizer to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cube_visualizer.interface.main import main

if __name__ == "__main__":
    main()
