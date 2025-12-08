#!/usr/bin/env python3
"""
Lecteur des facteurs de calibration stockés dans la sonde Narda EP600
"""

import serial
import time

def main():
    """Lecture des facteurs de calibration"""
    
    # Connexion série
    try:
        ser = serial.Serial('COM8', 9600, timeout=0.5)
        time.sleep(0.5)
        print("✓ Connecté à COM8")
    except:
        print("❌ Erreur connexion COM8")
        return
    
    print("📊 NARDA EP600 - Facteurs de calibration")
    print("="*60)
    
    print("🔍 Test de différentes commandes de calibration...")
    
    # Liste des commandes à tester
    test_commands = [
        ('#00?p*', 'Date calibration'),
        ('#00?c*', 'Facteur correction'),
        ('#00?k*', 'Facteur fréquence'), 
        ('#00?cal*', 'Calibration'),
        ('#00?freq*', 'Fréquence'),
        ('#00?f*', 'Fréquence courte'),
        ('#00?corr*', 'Correction'),
    ]
    
    for cmd, description in test_commands:
        print(f"\n{description} ({cmd}):")
        ser.reset_input_buffer()
        ser.write(cmd.encode())
        time.sleep(0.3)
        
        response = ser.read(100)
        text_response = response.decode('utf-8', errors='ignore').strip()
        
        if response:
            print(f"  Réponse: '{text_response}'")
            if len(response) > 20:
                print(f"  Hex: {response[:20].hex()}...")
            else:
                print(f"  Hex: {response.hex()}")
        else:
            print("  Pas de réponse")
    
    print(f"\n🧪 Test avec fréquences spécifiques...")
    
    # Tester en définissant différentes fréquences puis lire la correction
    test_frequencies = [1, 20, 100, 1000, 7500]  # 0.01, 0.2, 1.0, 10.0, 75.0 MHz
    
    for freq_code in test_frequencies:
        freq_mhz = freq_code / 100.0
        print(f"\nFréquence {freq_mhz} MHz:")
        
        # Définir la fréquence
        cmd_set = f"#00Sk{freq_code}*"
        ser.reset_input_buffer()
        ser.write(cmd_set.encode())
        time.sleep(0.5)
        
        # Lire le facteur de correction
        ser.reset_input_buffer()
        ser.write(b'#00?k*')
        time.sleep(0.3)
        
        response = ser.read(50)
        if response:
            text_response = response.decode('utf-8', errors='ignore').strip()
            print(f"  Facteur: '{text_response}'")
        else:
            print("  Pas de réponse")
    
    print()
    print("📊 TABLEAU DE RÉFÉRENCE:")
    print("-"*60)
    print("Fréq(MHz) | Facteur Lin | Facteur(dB)")
    print("-"*60)
    print("0.01      | 2.948       | 9.39")
    print("0.03      | 1.417       | 3.03") 
    print("0.2       | 1.040       | 0.34")
    print("1.0       | 1.022       | 0.19")
    print("200.0     | 0.979       | -0.18")
    print("7500.0    | 1.556       | 3.84")
    print("-"*60)
    
    ser.close()
    print("\n🔌 Connexion fermée")

if __name__ == "__main__":
    main()