"""Test minimal Arcus - connexion directe comme legacy controller"""
import os
from pylablib.devices import Arcus
import pylablib as pll

# DLL du fabricant, livrées avec le paquet arcus_performax_4ex
from arcus_performax_4ex import DLL_DIR
DEFAULT_DLL_PATH = str(DLL_DIR)

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

