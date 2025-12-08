#!/usr/bin/env python3
"""
Test des configurations de moyennage et filtrage pour optimiser le débit
"""

import serial
import time
import struct

class NardaConfigTest:
    def __init__(self, port='COM8', baudrate=9600):
        """Initialise la connexion série"""
        self.ser = serial.Serial(port, baudrate, timeout=0.2)
        time.sleep(1)
        print(f"✓ Connecté à {port}")
    
    def send_command(self, command, expect_response=True):
        """Envoie une commande et lit la réponse"""
        self.ser.reset_input_buffer()
        self.ser.write(command.encode())
        time.sleep(0.1)
        
        if expect_response:
            response = self.ser.read(50)
            return response.decode('utf-8', errors='ignore').strip()
        return "OK"
    
    def get_measurement_speed(self, num_samples=20):
        """Mesure la vitesse sur N échantillons"""
        times = []
        values = []
        
        for i in range(num_samples):
            start = time.perf_counter()
            self.ser.reset_input_buffer()
            self.ser.write(b'#00?T*')
            response = self.ser.read(6)
            end = time.perf_counter()
            
            times.append(end - start)
            
            if len(response) >= 5 and response[0:1] == b'T':
                try:
                    value = struct.unpack('<f', response[1:5])[0]
                    values.append(value)
                except:
                    pass
        
        if times:
            avg_time = sum(times) / len(times)
            freq = 1 / avg_time if avg_time > 0 else 0
            success_rate = len(values) / num_samples * 100
            return freq, avg_time * 1000, success_rate
        
        return 0, 0, 0
    
    def test_filter_settings(self):
        """Test différents réglages de filtre"""
        print("\n🔧 TEST DES FILTRES DIGITAUX")
        print("="*60)
        print(f"{'Filtre':<8} {'Fréq (Hz)':<12} {'Temps (ms)':<12} {'Succès %':<10}")
        print("-"*60)
        
        for filter_level in range(8):  # 0 à 7
            cmd = f"#00Sf{filter_level}*"
            print(f"Filter {filter_level}: ", end='')
            
            # Envoyer la commande de configuration
            result = self.send_command(cmd, expect_response=False)
            time.sleep(0.5)  # Attendre que la config soit prise en compte
            
            # Tester la vitesse
            freq, avg_time, success = self.get_measurement_speed(10)
            print(f"{filter_level:<8} {freq:<12.1f} {avg_time:<12.1f} {success:<10.1f}")
    
    def test_average_settings(self):
        """Test différents réglages de moyennage"""
        print("\n📊 TEST DES MOYENNAGES")
        print("="*60)
        print(f"{'Moyenne':<8} {'Fréq (Hz)':<12} {'Temps (ms)':<12} {'Succès %':<10}")
        print("-"*60)
        
        # Tenter différentes valeurs de moyennage
        for avg_level in [1, 4, 16, 32, 64]:
            cmd = f"#00Sa{avg_level}*"
            print(f"Avg {avg_level:2}: ", end='')
            
            # Envoyer la commande de configuration
            result = self.send_command(cmd, expect_response=False)
            time.sleep(0.5)
            
            # Tester la vitesse
            freq, avg_time, success = self.get_measurement_speed(10)
            print(f"{avg_level:<8} {freq:<12.1f} {avg_time:<12.1f} {success:<10.1f}")
    
    def test_reading_rate(self):
        """Test différents taux de lecture"""
        print("\n⏱️  TEST DES TAUX DE LECTURE")
        print("="*60)
        print(f"{'Rate (s)':<8} {'Fréq (Hz)':<12} {'Temps (ms)':<12} {'Succès %':<10}")
        print("-"*60)
        
        # Tenter différentes valeurs (en dixièmes de seconde)
        for rate_tenth in [1, 2, 5, 10]:  # 0.1s, 0.2s, 0.5s, 1.0s
            cmd = f"#00Sr{rate_tenth}*"
            rate_sec = rate_tenth / 10.0
            print(f"Rate {rate_sec:.1f}: ", end='')
            
            result = self.send_command(cmd, expect_response=False)
            time.sleep(1)
            
            freq, avg_time, success = self.get_measurement_speed(10)
            print(f"{rate_sec:<8.1f} {freq:<12.1f} {avg_time:<12.1f} {success:<10.1f}")
    
    def test_optimization_sequence(self):
        """Séquence d'optimisation pour vitesse maximale"""
        print("\n🚀 SÉQUENCE D'OPTIMISATION")
        print("="*60)
        
        # Configuration de base
        print("1. Configuration de base...")
        freq_base, time_base, success_base = self.get_measurement_speed(20)
        print(f"   Base: {freq_base:.1f} Hz, {time_base:.1f} ms, {success_base:.1f}%")
        
        # Filtre minimum
        print("2. Filtre minimum (0)...")
        self.send_command("#00Sf0*", expect_response=False)
        time.sleep(0.5)
        freq_filter, time_filter, success_filter = self.get_measurement_speed(20)
        print(f"   Filtre 0: {freq_filter:.1f} Hz, {time_filter:.1f} ms, {success_filter:.1f}%")
        
        # Moyennage minimum
        print("3. Moyennage minimum (1)...")
        self.send_command("#00Sa1*", expect_response=False)
        time.sleep(0.5)
        freq_avg, time_avg, success_avg = self.get_measurement_speed(20)
        print(f"   Avg 1: {freq_avg:.1f} Hz, {time_avg:.1f} ms, {success_avg:.1f}%")
        
        # Taux minimum
        print("4. Taux minimum (0.1s)...")
        self.send_command("#00Sr1*", expect_response=False)
        time.sleep(1)
        freq_rate, time_rate, success_rate = self.get_measurement_speed(20)
        print(f"   Rate 0.1s: {freq_rate:.1f} Hz, {time_rate:.1f} ms, {success_rate:.1f}%")
        
        print(f"\n📈 RÉSUMÉ OPTIMISATION:")
        print(f"   Base:      {freq_base:.1f} Hz")
        print(f"   Filtre 0:  {freq_filter:.1f} Hz ({freq_filter/freq_base*100-100:+.1f}%)")
        print(f"   Avg 1:     {freq_avg:.1f} Hz ({freq_avg/freq_base*100-100:+.1f}%)")
        print(f"   Rate 0.1s: {freq_rate:.1f} Hz ({freq_rate/freq_base*100-100:+.1f}%)")
    
    def test_other_commands(self):
        """Test d'autres commandes possibles"""
        print("\n🔍 TEST D'AUTRES COMMANDES")
        print("="*60)
        
        # Commandes à tester
        test_commands = [
            ("#00Se180*", "Auto-off 180s"),
            ("#00Se0*", "Auto-off désactivé"),
            ("#00?f*", "Fréquence actuelle"),
            ("#00?r*", "Taux de lecture"),
            ("#00Sk1000*", "Fréquence 100MHz")
        ]
        
        for cmd, description in test_commands:
            print(f"{description:<25}: ", end='')
            try:
                response = self.send_command(cmd)
                print(f"'{response}'")
            except:
                print("Erreur")
    
    def close(self):
        """Ferme la connexion"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("🔌 Connexion fermée")

def main():
    """Fonction principale"""
    print("⚙️  NARDA EP600 - TEST DE CONFIGURATION")
    print("="*60)
    
    try:
        narda = NardaConfigTest()
        
        # Tests de configuration
        narda.test_filter_settings()
        narda.test_average_settings() 
        narda.test_reading_rate()
        narda.test_optimization_sequence()
        narda.test_other_commands()
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrompu")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
    finally:
        try:
            narda.close()
        except:
            pass

if __name__ == "__main__":
    main()