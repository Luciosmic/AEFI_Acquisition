#!/usr/bin/env python3
"""
Test de performance : readline() vs read(taille_fixe)
Comparaison des méthodes de lecture série pour optimiser la communication avec la carte DDS/ADC
"""

import time
import serial
import threading
from datetime import datetime
import json
import sys
import os


class ReadMethodTester:
    """Testeur pour comparer les méthodes de lecture série"""
    
    def __init__(self, port="COM10", baudrate=1500000):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.lock = threading.Lock()
        
    def connect(self):
        """Établit la connexion série"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=8,
                stopbits=serial.STOPBITS_ONE,
                parity=serial.PARITY_NONE,
                timeout=1,
                write_timeout=1,
                exclusive=True
            )
            return True
        except Exception as e:
            print(f"Erreur de connexion: {e}")
            return False
    
    def disconnect(self):
        """Ferme la connexion"""
        if self.ser and self.ser.is_open:
            self.ser.close()
    
    def method_readline(self, m_value=127):
        """Méthode actuelle avec readline()"""
        if not self.ser or not self.ser.is_open:
            return False, "", 0
        
        start_time = time.perf_counter()
        
        with self.lock:
            try:
                # Envoyer commande
                command = f'm{m_value}*'
                self.ser.write(command.encode())
                
                # Première lecture : confirmation
                confirmation = self.ser.readline()
                # Seconde lecture : données
                data_response = self.ser.readline()
                
                end_time = time.perf_counter()
                duration_ms = (end_time - start_time) * 1000
                
                return True, data_response.decode('ascii', errors='ignore').rstrip('\r\n'), duration_ms
                
            except Exception as e:
                end_time = time.perf_counter()
                duration_ms = (end_time - start_time) * 1000
                return False, f"Erreur: {e}", duration_ms
    
    def method_fixed_size(self, m_value=127):
        """Méthode avec read() à taille fixe (style LabVIEW)"""
        if not self.ser or not self.ser.is_open:
            return False, "", 0
        
        start_time = time.perf_counter()
        
        with self.lock:
            try:
                # Envoyer commande
                command = f'm{m_value}*'
                self.ser.write(command.encode())
                
                # Première lecture : 9 caractères (confirmation)
                confirmation_raw = self.ser.read(9)
                
                # Seconde lecture : 99 caractères (données)
                data_raw = self.ser.read(99)
                
                end_time = time.perf_counter()
                duration_ms = (end_time - start_time) * 1000
                
                # Parser les données
                data_str = data_raw.decode('ascii', errors='ignore').rstrip('\r\n\x00')
                
                return True, data_str, duration_ms
                
            except Exception as e:
                end_time = time.perf_counter()
                duration_ms = (end_time - start_time) * 1000
                return False, f"Erreur: {e}", duration_ms
    
    def method_hybrid(self, m_value=127):
        """Méthode hybride : read() en bloc puis parsing"""
        if not self.ser or not self.ser.is_open:
            return False, "", 0
        
        start_time = time.perf_counter()
        
        with self.lock:
            try:
                # Envoyer commande
                command = f'm{m_value}*'
                self.ser.write(command.encode())
                
                # Lecture en bloc : 108 caractères (9+99)
                total_raw = self.ser.read(108)
                
                end_time = time.perf_counter()
                duration_ms = (end_time - start_time) * 1000
                
                # Parser : séparer confirmation et données
                total_str = total_raw.decode('ascii', errors='ignore')
                
                # Trouver le premier \n (fin de confirmation)
                first_newline = total_str.find('\n')
                if first_newline != -1:
                    data_part = total_str[first_newline + 1:].rstrip('\r\n\x00')
                    return True, data_part, duration_ms
                else:
                    return False, "Format invalide", duration_ms
                
            except Exception as e:
                end_time = time.perf_counter()
                duration_ms = (end_time - start_time) * 1000
                return False, f"Erreur: {e}", duration_ms
    
    def run_comparison_test(self, n_tests=100, m_value=127):
        """Lance un test de comparaison des 3 méthodes"""
        print(f"\n=== Test de comparaison des méthodes de lecture ===")
        print(f"Paramètres: n_tests={n_tests}, m_value={m_value}")
        print(f"Port: {self.port}, Baudrate: {self.baudrate}")
        
        if not self.connect():
            print("Impossible de se connecter au port série")
            return None
        
        methods = [
            ("readline", self.method_readline),
            ("fixed_size", self.method_fixed_size), 
            ("hybrid", self.method_hybrid)
        ]
        
        results = {}
        
        for method_name, method_func in methods:
            print(f"\n--- Test méthode: {method_name} ---")
            
            # Préchauffage
            print("Préchauffage...")
            for _ in range(5):
                method_func(m_value)
                time.sleep(0.01)
            
            # Test principal
            print(f"Test principal ({n_tests} acquisitions)...")
            times = []
            success_count = 0
            data_lengths = []
            
            for i in range(n_tests):
                success, data, duration_ms = method_func(m_value)
                times.append(duration_ms)
                
                if success and data.strip():
                    success_count += 1
                    data_lengths.append(len(data))
                
                if (i + 1) % 20 == 0:
                    print(f"  Progression: {i+1}/{n_tests}")
                
                time.sleep(0.005)  # Petit délai entre acquisitions
            
            # Calcul des statistiques
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            acquisition_rate = success_count / (sum(times) / 1000)  # acq/s
            success_rate = (success_count / n_tests) * 100
            avg_data_length = sum(data_lengths) / len(data_lengths) if data_lengths else 0
            
            results[method_name] = {
                "avg_time_ms": round(avg_time, 3),
                "min_time_ms": round(min_time, 3),
                "max_time_ms": round(max_time, 3),
                "acquisition_rate": round(acquisition_rate, 1),
                "success_rate": round(success_rate, 1),
                "avg_data_length": round(avg_data_length, 1),
                "total_time_s": round(sum(times) / 1000, 2)
            }
            
            print(f"  Temps moyen: {avg_time:.2f} ms")
            print(f"  Débit: {acquisition_rate:.1f} acq/s")
            print(f"  Taux de succès: {success_rate:.1f}%")
        
        self.disconnect()
        
        # Affichage du comparatif
        print(f"\n=== RÉSULTATS COMPARATIFS ===")
        print(f"{'Méthode':<12} {'Temps(ms)':<10} {'Débit(acq/s)':<12} {'Succès(%)':<10} {'Données(chars)':<15}")
        print("-" * 70)
        
        for method_name, stats in results.items():
            print(f"{method_name:<12} {stats['avg_time_ms']:<10} {stats['acquisition_rate']:<12} {stats['success_rate']:<10} {stats['avg_data_length']:<15}")
        
        # Déterminer la meilleure méthode
        best_method = min(results.keys(), key=lambda k: results[k]['avg_time_ms'])
        improvement_pct = {}
        
        baseline_time = results['readline']['avg_time_ms']
        for method_name, stats in results.items():
            if method_name != 'readline':
                improvement = ((baseline_time - stats['avg_time_ms']) / baseline_time) * 100
                improvement_pct[method_name] = improvement
        
        print(f"\n=== ANALYSE ===")
        print(f"Méthode la plus rapide: {best_method}")
        print(f"Temps baseline (readline): {baseline_time:.2f} ms")
        
        for method_name, improvement in improvement_pct.items():
            if improvement > 0:
                print(f"Amélioration {method_name}: +{improvement:.1f}% plus rapide")
            else:
                print(f"Performance {method_name}: {abs(improvement):.1f}% plus lente")
        
        # Sauvegarde des résultats
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        os.makedirs(results_dir, exist_ok=True)
        filename = os.path.join(results_dir, f"read_methods_comparison_{timestamp}.json")
        
        with open(filename, 'w') as f:
            json.dump({
                "test_params": {
                    "n_tests": n_tests,
                    "m_value": m_value,
                    "port": self.port,
                    "baudrate": self.baudrate,
                    "timestamp": timestamp
                },
                "results": results,
                "analysis": {
                    "best_method": best_method,
                    "improvements": improvement_pct
                }
            }, f, indent=2)
        
        print(f"\nRésultats sauvegardés dans: {filename}")
        
        return results


def main():
    """Fonction principale"""
    print("=== TEST DE PERFORMANCE: MÉTHODES DE LECTURE SÉRIE ===")
    print("Comparaison readline() vs read(taille_fixe) vs hybrid")
    
    # Configuration
    PORT = "COM10"  # Adapter selon votre configuration
    BAUDRATE = 1500000
    N_TESTS = 50  # Réduit pour un test rapide
    M_VALUE = 127
    
    # Demander confirmation
    response = input(f"\nLancer le test avec:\n"
                    f"- Port: {PORT}\n"
                    f"- Tests: {N_TESTS}\n"
                    f"- m_value: {M_VALUE}\n"
                    f"Continuer? (o/n): ")
    
    if response.lower() != 'o':
        print("Test annulé")
        return
    
    tester = ReadMethodTester(PORT, BAUDRATE)
    results = tester.run_comparison_test(N_TESTS, M_VALUE)
    
    if results:
        print("\n=== TEST TERMINÉ ===")
        print("Consultez les résultats détaillés dans le fichier JSON généré")
    else:
        print("\n=== ÉCHEC DU TEST ===")


if __name__ == "__main__":
    main() 