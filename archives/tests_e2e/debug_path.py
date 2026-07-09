import sys
import os

print(f"__file__: {__file__}")
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
print(f"Calculated src_path (level 2): {src_path}")
src_path_3 = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
print(f"Calculated src_path (level 3): {src_path_3}")

if os.path.exists(os.path.join(src_path, "application")):
    print("Level 2 looks correct (found application)")
elif os.path.exists(os.path.join(src_path_3, "application")):
    print("Level 3 looks correct (found application)")
else:
    print("Neither looks correct!")
