import sys
import os
import time
import csv
from datetime import datetime

# Pour exécution directe depuis /benchmark/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ArcusPerformaxPythonController.gui.components.ArcusPerformax4EXStage_StageManager import StageManager

manager = StageManager()

N_CYCLES = 10  # Nombre de cycles à réaliser
AXES = ['x', 'y']

# Récupérer la valeur max autorisée par le contrôleur pour chaque axe
axis_max = {'x': 30000, 'y': 30000}

INC_TO_UM = 43.6  # Facteur de conversion incrément -> µm

results = []

for i in range(N_CYCLES):
    print(f"\nCycle {i+1}/{N_CYCLES} : Homing X et Y...")
    # Homing simultané via home_both()
    manager.home_both()
    print("Homing terminé.")

    # Aller à la butée max pour chaque axe
    for axis in AXES:
        max_pos = axis_max[axis]
        print(f"Déplacement {axis.upper()} -> {max_pos}")
        manager.move_to(axis, max_pos)
        manager.wait_move(axis, timeout=60)
        pos_inc = manager.get_position(axis)
        pos_um = pos_inc * INC_TO_UM
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"Position max atteinte {axis.upper()} : {pos_inc} inc ({pos_um:.1f} µm)")
        results.append({
            'timestamp': timestamp,
            'cycle': i+1,
            'axe': axis.upper(),
            'position_max_inc': pos_inc,
            'position_max_um': pos_um
        })

    # Re-homing via home_both()
    manager.home_both()
    print("Re-homing terminé.")

# Export CSV
now = datetime.now().strftime('%Y-%m-%d_%H%M%S')
filename = f"caracterisation_butee_{now}.csv"
filepath = os.path.join(os.path.dirname(__file__), filename)

with open(filepath, 'w', newline='') as csvfile:
    fieldnames = ['timestamp', 'cycle', 'axe', 'position_max_inc', 'position_max_um']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for row in results:
        writer.writerow(row)

print(f"\nExport CSV terminé : {filepath}")
