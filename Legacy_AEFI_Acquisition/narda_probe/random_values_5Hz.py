#!/usr/bin/env python3
"""
Générateur de valeurs aléatoires à 5Hz pour comparaison visuelle
"""

import random
import time
from datetime import datetime

def main():
    """Affichage de valeurs aléatoires à 5Hz"""
    print("🎯 Générateur 5Hz - Comparaison avec ProbesManager")
    print("Ctrl+C pour arrêter\n")
    
    interval = 1/5  # 5Hz = 0.2 secondes
    count = 0
    
    try:
        while True:
            # Générer valeur aléatoire entre 9.00 et 9.03
            value = random.uniform(9.00, 9.03)
            
            # Afficher avec timestamp
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(f"{timestamp} | {value:.3f}")
            
            count += 1
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print(f"\n⏹️  Arrêté après {count} valeurs")
        print(f"   Fréquence: 5.0 Hz")

if __name__ == "__main__":
    main()