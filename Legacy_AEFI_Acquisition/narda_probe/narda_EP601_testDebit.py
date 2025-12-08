#!/usr/bin/env python3
"""
Test de débit maximal pour la sonde Narda EP600
Mesure la fréquence d'acquisition maximale
"""

import serial
import time
import struct
import statistics
from datetime import datetime

class NardaSpeedTest:
    def __init__(self, port='COM8', baudrate=9600):
        """Initialise la connexion série"""
        self.ser = serial.Serial(port, baudrate, timeout=0.1)
        time.sleep(1)
        print(f"✓ Connecté à {port} à {baudrate} bauds")
        
        # Test rapide de communication
        self.ser.reset_input_buffer()
        self.ser.write(b'#00?v*')
        time.sleep(0.2)
        response = self.ser.read(50)
        if b'EP600' in response:
            print(f"✓ Sonde détectée: {response.decode('utf-8', errors='ignore').strip()}")
        else:
            print("⚠️  Sonde non détectée, test en cours quand même...")
    
    def get_single_measurement(self):
        """
        Récupère une mesure unique le plus rapidement possible
        Returns: (valeur, temps_reponse) ou (None, temps_reponse)
        """
        start_time = time.perf_counter()
        
        # Vider le buffer et envoyer la commande
        self.ser.reset_input_buffer()
        self.ser.write(b'#00?T*')
        
        # Lire la réponse
        response = self.ser.read(6)  # 'T' + 4 bytes float + padding
        
        end_time = time.perf_counter()
        response_time = end_time - start_time
        
        if len(response) >= 5 and response[0:1] == b'T':
            try:
                # Décoder IEEE float Little Endian
                value = struct.unpack('<f', response[1:5])[0]
                return value, response_time
            except:
                return None, response_time
        
        return None, response_time
    
    def test_max_speed(self, duration=10):
        """
        Test la vitesse maximale pendant une durée donnée
        
        Args:
            duration: Durée du test en secondes
        """
        print(f"\n🚀 Test de vitesse maximale pendant {duration}s")
        print("="*60)
        
        measurements = []
        response_times = []
        errors = 0
        start_test = time.perf_counter()
        last_display = start_test
        
        while (time.perf_counter() - start_test) < duration:
            value, resp_time = self.get_single_measurement()
            response_times.append(resp_time)
            
            if value is not None:
                measurements.append(value)
            else:
                errors += 1
            
            # Affichage en temps réel (toutes les secondes)
            current_time = time.perf_counter()
            if current_time - last_display >= 1.0:
                elapsed = current_time - start_test
                total_attempts = len(response_times)
                success_rate = len(measurements) / total_attempts * 100
                avg_freq = total_attempts / elapsed
                
                print(f"t={elapsed:4.1f}s | Freq={avg_freq:6.1f} Hz | "
                      f"Succès={success_rate:5.1f}% | Valeur={value or 'ERR':>8}")
                last_display = current_time
        
        return measurements, response_times, errors
    
    def test_with_intervals(self, intervals=[0, 0.001, 0.01, 0.05, 0.1, 0.5]):
        """
        Test avec différents intervalles entre les mesures
        
        Args:
            intervals: Liste des intervalles à tester (en secondes)
        """
        print(f"\n📊 Test avec différents intervalles")
        print("="*80)
        print(f"{'Intervalle':<12} {'Freq théo':<12} {'Freq réelle':<12} {'Succès %':<10} {'Temps moy':<12}")
        print("-"*80)
        
        for interval in intervals:
            theo_freq = 1/(interval + 0.001) if interval > 0 else 1000  # Fréq théorique
            
            measurements = []
            response_times = []
            errors = 0
            
            # Test pendant 3 secondes
            start_time = time.perf_counter()
            while (time.perf_counter() - start_time) < 3.0:
                value, resp_time = self.get_single_measurement()
                response_times.append(resp_time)
                
                if value is not None:
                    measurements.append(value)
                else:
                    errors += 1
                
                if interval > 0:
                    time.sleep(interval)
            
            # Calculs
            total_time = time.perf_counter() - start_time
            real_freq = len(response_times) / total_time
            success_rate = len(measurements) / len(response_times) * 100
            avg_response = statistics.mean(response_times) * 1000  # en ms
            
            print(f"{interval:<12.3f} {theo_freq:<12.1f} {real_freq:<12.1f} "
                  f"{success_rate:<10.1f} {avg_response:<12.1f} ms")
    
    def analyze_results(self, measurements, response_times, errors, duration):
        """Analyse et affiche les résultats du test"""
        print(f"\n📈 RÉSULTATS DU TEST")
        print("="*50)
        
        total_attempts = len(response_times)
        successes = len(measurements)
        
        print(f"Durée du test:           {duration:.1f} s")
        print(f"Total tentatives:        {total_attempts}")
        print(f"Mesures réussies:        {successes}")
        print(f"Erreurs:                 {errors}")
        print(f"Taux de succès:          {successes/total_attempts*100:.1f} %")
        print()
        
        if response_times:
            avg_response = statistics.mean(response_times) * 1000
            min_response = min(response_times) * 1000
            max_response = max(response_times) * 1000
            
            print(f"Temps de réponse moyen:  {avg_response:.1f} ms")
            print(f"Temps de réponse min:    {min_response:.1f} ms")
            print(f"Temps de réponse max:    {max_response:.1f} ms")
            print()
        
        if successes > 0:
            freq_max = total_attempts / duration
            freq_effective = successes / duration
            
            print(f"Fréquence max tentée:    {freq_max:.1f} Hz")
            print(f"Fréquence effective:     {freq_effective:.1f} Hz")
            print()
        
        if measurements:
            print(f"Valeurs mesurées:")
            print(f"  Moyenne:               {statistics.mean(measurements):.2f} V/m")
            print(f"  Min:                   {min(measurements):.2f} V/m")
            print(f"  Max:                   {max(measurements):.2f} V/m")
            print(f"  Écart-type:            {statistics.stdev(measurements):.3f} V/m")
    
    def close(self):
        """Ferme la connexion"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("🔌 Connexion fermée")

def main():
    """Fonction principale"""
    print("⚡ NARDA EP600 - TEST DE DÉBIT MAXIMAL")
    print("="*60)
    
    try:
        # Initialisation
        narda = NardaSpeedTest()
        
        # Test 1: Vitesse maximale sans pause
        measurements, response_times, errors = narda.test_max_speed(duration=5)
        narda.analyze_results(measurements, response_times, errors, 5)
        
        # Test 2: Avec différents intervalles  
        narda.test_with_intervals()
        
        # Test 3: Test de stabilité sur plus longue durée
        print(f"\n🔄 Test de stabilité (30 secondes)")
        measurements, response_times, errors = narda.test_max_speed(duration=30)
        narda.analyze_results(measurements, response_times, errors, 30)
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
    finally:
        try:
            narda.close()
        except:
            pass

if __name__ == "__main__":
    main()