#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour le module de calibration des angles
"""

import sys
import os

# Ajouter le chemin src au sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'core'))

from EFImagingBench_angleCalibrationModule import AngleCalibrationCLI

def main():
    print("=== TEST DU MODULE DE CALIBRATION ===")
    print("Ce script teste l'initialisation du module de calibration")
    print("sans lancer la séquence complète.")
    print()
    
    try:
        # Créer une instance du calibrateur
        calibrator = AngleCalibrationCLI()
        
        # Tester l'initialisation
        print("[Test] Initialisation réussie!")
        print("[Test] Le module est prêt à être utilisé.")
        print()
        print("Pour lancer la calibration complète, exécutez:")
        print("python src/core/EFImagingBench_angleCalibrationModule.py")
        
    except Exception as e:
        print(f"[Test] Erreur: {e}")
        print("[Test] Vérifiez que tous les dépendances sont installées.")

if __name__ == "__main__":
    main()
