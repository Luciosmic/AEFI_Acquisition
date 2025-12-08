import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
from ArcusPerformaxPythonController.gui.components.ArcusPerformax4EXStage_StageManager import StageManager

manager = StageManager()  # ou StageManager(dll_path=...)

N = 100  # Nombre de requêtes pour le test
axis = "x"

# Benchmark get_position
start = time.perf_counter()
for _ in range(N):
    pos = manager.get_position(axis)
end = time.perf_counter()
dt = (end - start) / N
print(f"get_position: {dt*1000:.2f} ms/appel, {1/dt:.1f} Hz")

# Benchmark get_current_axis_speed
start = time.perf_counter()
for _ in range(N):
    speed = manager.get_current_axis_speed(axis)
end = time.perf_counter()
dt = (end - start) / N
print(f"get_current_axis_speed: {dt*1000:.2f} ms/appel, {1/dt:.1f} Hz")
