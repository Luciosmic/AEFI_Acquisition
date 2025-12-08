#!/usr/bin/env python3
"""
Script de lancement pour l'interface graphique LSM9D
"""

import sys
import os

# Ajouter les répertoires nécessaires au path Python
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# Ajouter le répertoire parent (LSM9D) et les sous-dossiers
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(parent_dir, 'instrument'))

try:
    from LSM9D_GUI_v2 import main
    print("🚀 Lancement de l'interface graphique LSM9D...")
    main()
except ImportError as e:
    print("❌ Erreur d'import:", e)
    print("\n💡 Assurez-vous d'avoir installé les dépendances:")
    print("   pip install PyQt5 pyqtgraph pyserial numpy")
    print("\n📁 Structure requise:")
    print("   LSM9D/")
    print("   ├── interface/")
    print("   │   ├── LSM9D_GUI.py")
    print("   │   └── run_gui.py")
    print("   └── instrument/")
    print("       └── LSM9D_Backend.py")
    input("\nAppuyez sur Entrée pour fermer...")
except Exception as e:
    print("❌ Erreur:", e)
    input("\nAppuyez sur Entrée pour fermer...") 