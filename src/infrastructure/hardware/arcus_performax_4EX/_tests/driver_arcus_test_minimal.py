"""Test minimal Arcus - connexion directe comme legacy controller"""
import os
from pylablib.devices import Arcus
import pylablib as pll

# Chemin DLL comme legacy
DEFAULT_DLL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "DLL64"))

if not os.path.isdir(DEFAULT_DLL_PATH):
    print(f"ERROR: DLL path not found: {DEFAULT_DLL_PATH}")
    exit(1)

pll.par["devices/dlls/arcus_performax"] = DEFAULT_DLL_PATH
print(f"DLL path set to: {pll.par['devices/dlls/arcus_performax']}")

try:
    print("Connecting to Arcus...")
    stage = Arcus.Performax4EXStage()
    print("✓ Connection successful!")
    print(f"Stage info: {stage.get_device_info()}")
    stage.close()
except Exception as e:
    print(f"✗ Connection failed: {e}")
    import traceback
    traceback.print_exc()

