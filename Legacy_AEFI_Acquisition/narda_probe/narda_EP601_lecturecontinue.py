#!/usr/bin/env python3
"""
Lecteur minimal et stable pour comparaison avec ProbesManager
"""

import serial
import time
import struct
from datetime import datetime
import math


def main():
    """Lecture continue des valeurs Narda EP600"""
    
    # Connexion série
    try:
        ser = serial.Serial('COM8', 9600, timeout=0.2)
        time.sleep(0.5)
        print("✓ Connecté à COM8")
    except:
        print("❌ Erreur connexion COM8")
        return
    
    print("🔵 NARDA EP600 - Lecture continue")
    print("Ctrl+C pour arrêter\n")
    
    count = 0
    
    try:
        while True:
            # Lecture de mesure
            ser.reset_input_buffer()
            ser.write(b'#00?T*')
            response = ser.read(6)
            
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            if len(response) >= 5 and response[0:1] == b'T':
                try:
                    square_value = struct.unpack('<f', response[1:5])[0]
                    value = math.sqrt(square_value)
                    print(f"{timestamp} | {value:7.2f} V/m")
                except:
                    print(f"{timestamp} | ERREUR DECODE")
            else:
                print(f"{timestamp} | ERREUR COMM")
            
            count += 1
            time.sleep(0.2)  # 5Hz
            
    except KeyboardInterrupt:
        print(f"\n⏹️  Arrêté après {count} lectures")
    finally:
        ser.close()
        print("🔌 Connexion fermée")

if __name__ == "__main__":
    main()