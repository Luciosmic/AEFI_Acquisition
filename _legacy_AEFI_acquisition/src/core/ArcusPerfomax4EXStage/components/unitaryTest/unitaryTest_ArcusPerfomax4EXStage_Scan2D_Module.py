import os
import sys
import inspect

# Prépare le path pour importer le module frère dans components/
CURRENT_DIR = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
COMPONENTS_DIR = os.path.dirname(CURRENT_DIR)
if COMPONENTS_DIR not in sys.path:
    sys.path.insert(0, COMPONENTS_DIR)

# Import après configuration du path
from ArcusPerfomax4EXStage_Scan2D_Module import Scan2DConfigurator


def demo_scan2d():
    # Paramètres de test simples
    x_min, x_max = 0, 10
    y_min, y_max = 0, 5
    N = 3
    mode = 'E'  # 'E' (unidirectionnel) ou 'S' (aller-retour)
    timer_ms = 100

    cfg = Scan2DConfigurator(x_min, x_max, y_min, y_max, N, y_nb=N, timer_ms=timer_ms, mode=mode)

    print("=== to_dict ===")
    print(cfg.to_dict())

    print("\n=== get_flyscan_lines ===")
    for line in cfg.get_flyscan_lines():
        print(line)  # (x, y_start, y_end)

    print("\n=== get_segmented_trajectory ===")
    segments = cfg.get_segmented_trajectory()
    for s in segments:
        print(s)

    print("\n=== get_points_from_segments ===")
    points = cfg.get_points_from_segments(segments)
    for p in points:
        print(p)  # (x, y, segment_info)

    print("\n=== get_progress examples (idx -> (line, col)) ===")
    for idx in range(0, 6):
        print(idx, '->', cfg.get_progress(idx))


if __name__ == "__main__":
    demo_scan2d()


