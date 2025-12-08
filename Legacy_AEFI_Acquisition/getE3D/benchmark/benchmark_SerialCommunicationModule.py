#!/usr/bin/env python3
"""
Benchmark dédié à la classe SerialCommunicator optimisée
Teste les performances de communication avec la carte DDS/ADC en utilisant uniquement la classe
"""

import time
import statistics
from typing import List, Dict
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import os
import json
import csv
import sys
import serial.tools.list_ports

# Ajouter le chemin vers les instruments
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "instruments"))
from AD9106_ADS131A04_SerialCommunicationModule import SerialCommunicator

class SerialCommunicatorBenchmark:
    def __init__(self, port: str = "COM10", baudrate: int = 1500000):
        self.port = port
        self.baudrate = baudrate
        self.comm = SerialCommunicator()
        self.results = {}
        
    @staticmethod
    def detect_available_ports():
        """Détecte les ports série disponibles"""
        ports = serial.tools.list_ports.comports()
        available_ports = []
        
        for port in ports:
            port_info = {
                'device': port.device,
                'description': port.description,
                'manufacturer': port.manufacturer or 'Inconnu'
            }
            available_ports.append(port_info)
            
        return available_ports
    
    def auto_detect_port(self):
        """Tente de détecter automatiquement le bon port"""
        print("🔍 Détection automatique des ports série...")
        
        available_ports = self.detect_available_ports()
        
        if not available_ports:
            print("❌ Aucun port série détecté")
            return False
            
        print(f"📡 {len(available_ports)} port(s) détecté(s):")
        for i, port in enumerate(available_ports):
            print(f"   {i+1}. {port['device']} - {port['description']} ({port['manufacturer']})")
        
        # Si un seul port, l'utiliser automatiquement
        if len(available_ports) == 1:
            self.port = available_ports[0]['device']
            print(f"✅ Port sélectionné automatiquement: {self.port}")
            return True
            
        # Sinon, demander à l'utilisateur
        try:
            choix = int(input(f"Choisissez un port (1-{len(available_ports)}) : ")) - 1
            if 0 <= choix < len(available_ports):
                self.port = available_ports[choix]['device']
                print(f"✅ Port sélectionné: {self.port}")
                return True
            else:
                print("❌ Choix invalide")
                return False
        except (ValueError, KeyboardInterrupt):
            print("❌ Sélection annulée")
            return False
        
    def connect(self) -> bool:
        """Établit la connexion avec la carte"""
        success, message = self.comm.connect(self.port, self.baudrate)
        if success:
            print(f"✅ Connexion établie sur {self.port} à {self.baudrate} bps")
            return True
        else:
            print(f"❌ Erreur de connexion sur {self.port}: {message}")
            
            # Proposer la détection automatique
            response = input("🔍 Voulez-vous essayer la détection automatique de port ? (o/n) : ").strip().lower()
            if response in ['o', 'oui', 'y', 'yes']:
                if self.auto_detect_port():
                    # Réessayer la connexion avec le nouveau port
                    success, message = self.comm.connect(self.port, self.baudrate)
                    if success:
                        print(f"✅ Connexion établie sur {self.port} à {self.baudrate} bps")
                        return True
                    else:
                        print(f"❌ Échec de connexion même avec le port détecté: {message}")
            
            return False
        
    def disconnect(self):
        """Ferme la connexion"""
        self.comm.disconnect()
        print("🔌 Connexion fermée")
    
    def benchmark_acquisition_latency(self, m_value: int = 127, num_tests: int = 100) -> Dict:
        """Mesure la latence des acquisitions pour un facteur de moyennage donné"""
        print(f"\n📊 Benchmark latence d'acquisition (m={m_value}, {num_tests} tests)")
        
        latencies = []
        successful_tests = 0
        
        for i in range(num_tests):
            cmd = f"m{m_value}"
            start_time = time.perf_counter()
            success, response = self.comm.send_command(cmd)
            end_time = time.perf_counter()
            
            if success and response:
                latency = (end_time - start_time) * 1000  # Conversion en ms
                latencies.append(latency)
                successful_tests += 1
            
            # Affichage du progrès
            if (i + 1) % 20 == 0:
                print(f"   Progrès: {i + 1}/{num_tests}")
        
        if latencies:
            results = {
                'latencies': latencies,
                'mean_latency': statistics.mean(latencies),
                'min_latency': min(latencies),
                'max_latency': max(latencies),
                'std_latency': statistics.stdev(latencies) if len(latencies) > 1 else 0,
                'successful_tests': successful_tests,
                'success_rate': (successful_tests / num_tests) * 100,
                'm_value': m_value,
                'total_tests': num_tests
            }
            
            print(f"   ✅ Latence moyenne: {results['mean_latency']:.2f} ms")
            print(f"   📈 Latence min/max: {results['min_latency']:.2f} / {results['max_latency']:.2f} ms")
            print(f"   📊 Écart-type: {results['std_latency']:.2f} ms")
            print(f"   🎯 Taux de succès: {results['success_rate']:.1f}% ({successful_tests}/{num_tests})")
            
            return results
        else:
            print("   ❌ Aucune mesure valide obtenue")
            return None
    
    def benchmark_acquisition_throughput(self, m_value: int = 127, duration: float = 10.0) -> Dict:
        """Mesure le débit d'acquisition pour un facteur de moyennage donné"""
        print(f"\n🚀 Benchmark débit d'acquisition (m={m_value}, {duration}s)")
        
        start_time = time.time()
        latencies = []
        successful_acq = 0
        total_acq = 0
        first_errors = []  # Stocker les premières erreurs pour diagnostic
        
        while (time.time() - start_time) < duration:
            cmd = f"m{m_value}"
            cmd_start = time.perf_counter()
            success, response = self.comm.send_command(cmd)
            cmd_end = time.perf_counter()
            
            total_acq += 1
            if success and response:
                successful_acq += 1
                latency = (cmd_end - cmd_start) * 1000
                latencies.append(latency)
            else:
                # Collecter les premières erreurs pour diagnostic
                if len(first_errors) < 5:
                    first_errors.append({
                        'attempt': total_acq,
                        'success': success,
                        'response': response[:50] if response else 'None'  # Limiter la longueur
                    })
        
        elapsed_time = time.time() - start_time
        throughput = successful_acq / elapsed_time
        
        # Afficher les erreurs si il y en a
        if first_errors and successful_acq < total_acq * 0.5:  # Si moins de 50% de succès
            print(f"   ⚠️  Premières erreurs de communication détectées:")
            for error in first_errors:
                print(f"      Tentative {error['attempt']}: success={error['success']}, response='{error['response']}'")
        
        results = {
            'throughput': throughput,
            'successful_acq': successful_acq,
            'total_acq': total_acq,
            'success_rate': (successful_acq / total_acq) * 100 if total_acq > 0 else 0,
            'elapsed_time': elapsed_time,
            'latencies': latencies,
            'mean_latency': statistics.mean(latencies) if latencies else 0,
            'm_value': m_value,
            'first_errors': first_errors
        }
        
        print(f"   🎯 Débit: {results['throughput']:.2f} acquisitions/s")
        print(f"   ✅ Acquisitions réussies: {successful_acq}/{total_acq} ({results['success_rate']:.1f}%)")
        print(f"   ⏱️ Latence moyenne: {results['mean_latency']:.2f} ms")
        
        return results
    
    def benchmark_data_quality(self, m_value: int = 127, num_samples: int = 100) -> Dict:
        """Test séparé pour évaluer la qualité des données sans impacter les performances"""
        print(f"\n🔍 Test qualité des données (m={m_value}, {num_samples} échantillons)")
        
        valid_data = 0
        invalid_data = 0
        validation_errors = []
        sample_responses = []
        
        for i in range(num_samples):
            cmd = f"m{m_value}"
            success, response = self.comm.send_command(cmd)
            
            if success and response:
                # Validation de la qualité des données
                is_valid, validation_msg = self.validate_acquisition_data(response)
                if is_valid:
                    valid_data += 1
                    # Garder quelques exemples de données valides
                    if len(sample_responses) < 3:
                        sample_responses.append(response)
                else:
                    invalid_data += 1
                    # Collecter les erreurs de validation
                    if len(validation_errors) < 5:
                        validation_errors.append({
                            'sample': i + 1,
                            'response': response[:100],  # Limiter pour l'affichage
                            'error': validation_msg
                        })
            
            # Affichage du progrès
            if (i + 1) % 20 == 0:
                print(f"   Progrès: {i + 1}/{num_samples}")
        
        total_valid_attempts = valid_data + invalid_data
        quality_rate = (valid_data / total_valid_attempts) * 100 if total_valid_attempts > 0 else 0
        
        # Afficher les erreurs de validation
        if validation_errors:
            print(f"   ⚠️  Erreurs de validation détectées:")
            for error in validation_errors:
                print(f"      Échantillon {error['sample']}: {error['error']}")
                print(f"         Réponse: '{error['response']}'")
        
        # Afficher quelques exemples de données valides
        if sample_responses:
            print(f"   ✅ Exemples de données valides:")
            for i, resp in enumerate(sample_responses):
                print(f"      {i+1}: {resp}")
        
        results = {
            'valid_data': valid_data,
            'invalid_data': invalid_data,
            'total_attempts': total_valid_attempts,
            'quality_rate': quality_rate,
            'validation_errors': validation_errors,
            'sample_responses': sample_responses,
            'm_value': m_value,
            'num_samples': num_samples
        }
        
        print(f"   📊 Qualité des données: {valid_data}/{total_valid_attempts} valides ({quality_rate:.1f}%)")
        
        return results
    
    def benchmark_fast_acquisition_m127(self, duration: float = 10.0) -> Dict:
        """Mesure le débit avec la méthode fast_acquisition_m127 optimisée"""
        print(f"\n⚡ Benchmark fast_acquisition_m127 ({duration}s)")
        
        start_time = time.time()
        latencies = []
        successful_acq = 0
        total_acq = 0
        first_errors = []  # Stocker les premières erreurs pour diagnostic
        
        while (time.time() - start_time) < duration:
            cmd_start = time.perf_counter()
            success, response = self.comm.fast_acquisition_m127()
            cmd_end = time.perf_counter()
            
            total_acq += 1
            if success and response:
                successful_acq += 1
                latency = (cmd_end - cmd_start) * 1000
                latencies.append(latency)
            else:
                # Collecter les premières erreurs pour diagnostic
                if len(first_errors) < 5:
                    first_errors.append({
                        'attempt': total_acq,
                        'success': success,
                        'response': response[:50] if response else 'None'  # Limiter la longueur
                    })
        
        elapsed_time = time.time() - start_time
        throughput = successful_acq / elapsed_time
        
        # Afficher les erreurs si il y en a
        if first_errors and successful_acq < total_acq * 0.5:  # Si moins de 50% de succès
            print(f"   ⚠️  Premières erreurs détectées:")
            for error in first_errors:
                print(f"      Tentative {error['attempt']}: success={error['success']}, response='{error['response']}'")
        
        results = {
            'throughput': throughput,
            'successful_acq': successful_acq,
            'total_acq': total_acq,
            'success_rate': (successful_acq / total_acq) * 100 if total_acq > 0 else 0,
            'elapsed_time': elapsed_time,
            'latencies': latencies,
            'mean_latency': statistics.mean(latencies) if latencies else 0,
            'm_value': 127,
            'method': 'fast_acquisition_m127',
            'first_errors': first_errors
        }
        
        print(f"   ⚡ Débit: {results['throughput']:.2f} acquisitions/s")
        print(f"   ✅ Acquisitions réussies: {successful_acq}/{total_acq} ({results['success_rate']:.1f}%)")
        print(f"   ⏱️ Latence moyenne: {results['mean_latency']:.2f} ms")
        
        return results
    
    def compare_acquisition_methods(self, duration: float = 10.0) -> Dict:
        """Compare les performances entre send_command et fast_acquisition_m127"""
        print(f"\n🔄 Comparaison des méthodes d'acquisition (m=127)")
        
        # Établir la connexion si pas déjà connectée
        if not self.comm.ser or not self.comm.ser.is_open:
            print("📡 Tentative de connexion...")
            if not self.connect():
                print("❌ Impossible de se connecter - arrêt du test")
                return None
        
        try:
            # Test 1: Méthode standard
            print("\n1. Test avec send_command standard...")
            results_standard = self.benchmark_acquisition_throughput(m_value=127, duration=duration)
            
            # Test 2: Méthode optimisée
            print("\n2. Test avec fast_acquisition_m127...")
            results_fast = self.benchmark_fast_acquisition_m127(duration=duration)
            
            # Analyse comparative
            if results_standard and results_fast:
                print("\n=== ANALYSE COMPARATIVE ===")
                
                # Vérifier que nous avons des données valides
                if results_standard['mean_latency'] == 0 or results_fast['mean_latency'] == 0:
                    print("⚠️  ERREUR: Pas de données valides pour l'analyse")
                    print(f"   Standard: {results_standard['successful_acq']} acquisitions réussies")
                    print(f"   Fast: {results_fast['successful_acq']} acquisitions réussies")
                    
                    # Diagnostique des erreurs
                    if results_standard['successful_acq'] == 0:
                        print("   🔍 Test de diagnostic pour send_command...")
                        test_success, test_response = self.comm.send_command("m1")
                        print(f"      Test m1: success={test_success}, response='{test_response}'")
                    
                    if results_fast['successful_acq'] == 0:
                        print("   🔍 Test de diagnostic pour fast_acquisition_m127...")
                        test_success, test_response = self.comm.fast_acquisition_m127()
                        print(f"      Test fast: success={test_success}, response='{test_response}'")
                    
                    return {
                        'standard': results_standard,
                        'fast': results_fast,
                        'error': 'Aucune acquisition réussie',
                        'diagnostics': {
                            'standard_success_rate': results_standard['success_rate'],
                            'fast_success_rate': results_fast['success_rate']
                        }
                    }
                
                # Calcul des améliorations seulement si nous avons des données valides
                latency_improvement = ((results_standard['mean_latency'] - results_fast['mean_latency']) / 
                                     results_standard['mean_latency']) * 100
                throughput_improvement = ((results_fast['throughput'] - results_standard['throughput']) / 
                                        results_standard['throughput']) * 100
                
                print(f"FAST_ACQUISITION_M127 vs SEND_COMMAND:")
                print(f"  Latence: {latency_improvement:+.1f}% ({results_fast['mean_latency']:.2f} vs {results_standard['mean_latency']:.2f} ms)")
                print(f"  Débit: {throughput_improvement:+.1f}% ({results_fast['throughput']:.2f} vs {results_standard['throughput']:.2f} acq/s)")
                
                return {
                    'standard': results_standard,
                    'fast': results_fast,
                    'improvements': {
                        'latency_improvement_percent': latency_improvement,
                        'throughput_improvement_percent': throughput_improvement,
                        'latency_gain_ms': results_standard['mean_latency'] - results_fast['mean_latency'],
                        'throughput_gain_acq_per_s': results_fast['throughput'] - results_standard['throughput']
                    }
                }
            else:
                print("⚠️  ERREUR: Impossible d'obtenir des résultats de benchmark")
                return None
                
        finally:
            # Fermer la connexion proprement
            self.disconnect()
    
    def benchmark_configuration_speed(self, num_tests: int = 100) -> Dict:
        """Mesure la vitesse des commandes de configuration"""
        print(f"\n⚙️ Benchmark vitesse de configuration ({num_tests} tests)")
        
        config_tests = [
            ("set_frequency", lambda: self.comm.set_dds_frequency(1000)),
            ("set_gain", lambda: self.comm.set_dds_gain(1, 10000)),
            ("set_phase", lambda: self.comm.set_dds_phase(1, 0)),
            ("set_mode", lambda: self.comm.set_dds1_mode("AC"))
        ]
        
        results = {}
        
        for test_name, test_func in config_tests:
            print(f"   Testing {test_name}...")
            latencies = []
            successful_tests = 0
            
            for _ in range(num_tests):
                start_time = time.perf_counter()
                success, _ = test_func()
                end_time = time.perf_counter()
                
                if success:
                    latency = (end_time - start_time) * 1000
                    latencies.append(latency)
                    successful_tests += 1
            
            if latencies:
                results[test_name] = {
                    'latencies': latencies,
                    'mean_latency': statistics.mean(latencies),
                    'min_latency': min(latencies),
                    'max_latency': max(latencies),
                    'std_latency': statistics.stdev(latencies) if len(latencies) > 1 else 0,
                    'successful_tests': successful_tests,
                    'success_rate': (successful_tests / num_tests) * 100
                }
                
                print(f"      ✅ {test_name}: {results[test_name]['mean_latency']:.2f} ms (±{results[test_name]['std_latency']:.2f})")
        
        return results
    
    def benchmark_m_value_sweep(self, m_values: List[int] = None, duration: float = 5.0) -> Dict:
        """Teste le débit pour différents facteurs de moyennage"""
        if m_values is None:
            m_values = [1, 2, 4, 8, 16, 32, 64, 127]
        
        print(f"\n🔄 Benchmark sweep facteur de moyennage")
        print(f"   Valeurs testées: {m_values}")
        print(f"   Durée par test: {duration}s")
        
        sweep_results = []
        
        for m_value in m_values:
            print(f"   Testing m={m_value}...")
            result = self.benchmark_acquisition_throughput(m_value, duration)
            if result:
                sweep_results.append(result)
        
        return {
            'sweep_results': sweep_results,
            'm_values': m_values,
            'duration': duration
        }
    
    def benchmark_m_value_with_delay(self, m_values: List[int] = None, duration: float = 5.0, delay_ms: float = 0.0) -> Dict:
        """Teste le débit avec un délai entre les commandes pour analyser l'overhead"""
        if m_values is None:
            m_values = [1, 2, 4, 8, 16, 32, 64, 127]
        
        print(f"\n🔄 Benchmark avec délai entre commandes")
        print(f"   Valeurs testées: {m_values}")
        print(f"   Durée par test: {duration}s")
        print(f"   Délai entre commandes: {delay_ms}ms")
        
        sweep_results = []
        
        for m_value in m_values:
            print(f"   Testing m={m_value} avec délai {delay_ms}ms...")
            
            start_time = time.time()
            latencies = []
            successful_acq = 0
            total_acq = 0
            
            while (time.time() - start_time) < duration:
                cmd = f"m{m_value}"
                cmd_start = time.perf_counter()
                success, response = self.comm.send_command(cmd)
                cmd_end = time.perf_counter()
                
                total_acq += 1
                if success and response:
                    successful_acq += 1
                    latency = (cmd_end - cmd_start) * 1000
                    latencies.append(latency)
                
                # Délai optionnel entre les commandes
                if delay_ms > 0:
                    time.sleep(delay_ms / 1000.0)
            
            elapsed_time = time.time() - start_time
            throughput = successful_acq / elapsed_time
            
            result = {
                'throughput': throughput,
                'successful_acq': successful_acq,
                'total_acq': total_acq,
                'success_rate': (successful_acq / total_acq) * 100 if total_acq > 0 else 0,
                'elapsed_time': elapsed_time,
                'latencies': latencies,
                'mean_latency': statistics.mean(latencies) if latencies else 0,
                'm_value': m_value,
                'delay_ms': delay_ms
            }
            
            print(f"      🎯 m={m_value}: {result['throughput']:.2f} acq/s (latence: {result['mean_latency']:.1f}ms)")
            sweep_results.append(result)
        
        return {
            'sweep_results': sweep_results,
            'm_values': m_values,
            'duration': duration,
            'delay_ms': delay_ms
        }
    
    def analyze_overhead_vs_acquisition_time(self, m_values: List[int] = None) -> Dict:
        """Analyse la décomposition du temps entre overhead et temps d'acquisition réel"""
        if m_values is None:
            m_values = [1, 8, 32, 127]
        
        print(f"\n🔬 Analyse décomposition des temps")
        print(f"   Mesure séparée: overhead communication vs temps acquisition")
        
        results = []
        
        for m_value in m_values:
            print(f"   Analysing m={m_value}...")
            
            # Test 1: Mesure de la latence pure (10 mesures précises)
            latencies_pure = []
            for _ in range(10):
                cmd = f"m{m_value}"
                start_time = time.perf_counter()
                success, response = self.comm.send_command(cmd)
                end_time = time.perf_counter()
                
                if success and response:
                    latency = (end_time - start_time) * 1000
                    latencies_pure.append(latency)
            
            # Test 2: Estimation du temps d'acquisition théorique
            # Basé sur les spécifications de l'ADC (oversampling_ratio = 32, freq_echantillonnage ≈ 16MHz)
            theoretical_acq_time = m_value * (32 / 16000)  # en ms (approximation)
            
            mean_latency = statistics.mean(latencies_pure) if latencies_pure else 0
            estimated_overhead = mean_latency - theoretical_acq_time
            
            result = {
                'm_value': m_value,
                'measured_latency': mean_latency,
                'theoretical_acq_time': theoretical_acq_time,
                'estimated_overhead': estimated_overhead,
                'overhead_percentage': (estimated_overhead / mean_latency * 100) if mean_latency > 0 else 0,
                'num_samples': len(latencies_pure)
            }
            
            results.append(result)
            
            print(f"      Latence mesurée: {mean_latency:.2f}ms")
            print(f"      Temps acq théorique: {theoretical_acq_time:.2f}ms") 
            print(f"      Overhead estimé: {estimated_overhead:.2f}ms ({result['overhead_percentage']:.1f}%)")
        
        return {
            'analysis_results': results,
            'm_values': m_values
        }
    
    def benchmark_m_value_sweep_detailed(self, m_values: List[int] = None, num_samples: int = 50) -> Dict:
        """
        Teste le débit pour différents facteurs de moyennage avec analyse détaillée
        Mesure les temps individuels pour mieux comprendre l'overhead vs temps d'acquisition
        """
        if m_values is None:
            m_values = [1, 2, 4, 8, 16, 32, 64, 127]
        
        print(f"\n🔬 Benchmark détaillé - sweep facteur de moyennage")
        print(f"   Valeurs testées: {m_values}")
        print(f"   Échantillons par test: {num_samples}")
        
        detailed_results = []
        
        for m_value in m_values:
            print(f"\n   📊 Test détaillé m={m_value}...")
            
            # Mesures individuelles précises
            individual_latencies = []
            successful_acq = 0
            
            for i in range(num_samples):
                cmd = f"m{m_value}"
                cmd_start = time.perf_counter()
                success, response = self.comm.send_command(cmd)
                cmd_end = time.perf_counter()
                
                if success and response:
                    successful_acq += 1
                    latency = (cmd_end - cmd_start) * 1000  # en ms
                    individual_latencies.append(latency)
                
                # Petite pause entre les mesures pour éviter la saturation
                time.sleep(0.01)
            
            if individual_latencies:
                # Calculs statistiques
                mean_latency = statistics.mean(individual_latencies)
                min_latency = min(individual_latencies)
                max_latency = max(individual_latencies)
                std_latency = statistics.stdev(individual_latencies) if len(individual_latencies) > 1 else 0
                
                # Estimation du temps d'acquisition théorique
                # Basé sur : temps_acq = m_value * (oversampling_ratio / freq_echantillonnage)
                # Avec oversampling_ratio = 32 et freq_echantillonnage ≈ 16MHz
                theoretical_acq_time = m_value * (32 / 16000)  # en ms
                
                # Calcul de l'overhead (différence entre temps mesuré et théorique)
                estimated_overhead = mean_latency - theoretical_acq_time
                overhead_percentage = (estimated_overhead / mean_latency * 100) if mean_latency > 0 else 0
                
                # Calcul du débit effectif
                throughput = 1000 / mean_latency  # acquisitions par seconde
                
                result = {
                    'm_value': m_value,
                    'individual_latencies': individual_latencies,
                    'mean_latency': mean_latency,
                    'min_latency': min_latency,
                    'max_latency': max_latency,
                    'std_latency': std_latency,
                    'theoretical_acq_time': theoretical_acq_time,
                    'estimated_overhead': estimated_overhead,
                    'overhead_percentage': overhead_percentage,
                    'throughput': throughput,
                    'successful_acq': successful_acq,
                    'total_samples': num_samples,
                    'success_rate': (successful_acq / num_samples) * 100
                }
                
                print(f"      ✅ Latence moyenne: {mean_latency:.2f}ms (±{std_latency:.2f})")
                print(f"      🧮 Temps théorique: {theoretical_acq_time:.2f}ms")
                print(f"      ⚙️ Overhead estimé: {estimated_overhead:.2f}ms ({overhead_percentage:.1f}%)")
                print(f"      🚀 Débit: {throughput:.2f} acq/s")
                
                detailed_results.append(result)
            else:
                print(f"      ❌ Aucune mesure valide pour m={m_value}")
        
        # Analyse comparative
        if len(detailed_results) >= 2:
            print(f"\n=== ANALYSE COMPARATIVE DÉTAILLÉE ===")
            
            # Comparer les overheads
            overheads = [r['estimated_overhead'] for r in detailed_results]
            mean_overhead = statistics.mean(overheads)
            std_overhead = statistics.stdev(overheads) if len(overheads) > 1 else 0
            
            print(f"📊 Overhead moyen: {mean_overhead:.2f}ms (±{std_overhead:.2f})")
            
            # Vérifier si l'overhead est constant (ce qui expliquerait pourquoi le débit ne change pas beaucoup)
            if std_overhead < mean_overhead * 0.1:  # Si écart-type < 10% de la moyenne
                print("⚠️  L'overhead semble constant - ceci explique pourquoi le débit change peu")
            
            # Comparer les temps théoriques vs mesurés
            print(f"\n📈 Évolution temps théorique vs mesuré:")
            for r in detailed_results:
                efficiency = (r['theoretical_acq_time'] / r['mean_latency']) * 100
                print(f"   m={r['m_value']:3d}: {r['theoretical_acq_time']:5.2f}ms théorique vs {r['mean_latency']:5.2f}ms mesuré (efficacité: {efficiency:.1f}%)")
        
        return {
            'detailed_results': detailed_results,
            'm_values': m_values,
            'num_samples': num_samples,
            'analysis': {
                                 'overhead_analysis': {
                     'mean_overhead': statistics.mean([r['estimated_overhead'] for r in detailed_results]),
                     'std_overhead': statistics.stdev([r['estimated_overhead'] for r in detailed_results]) if len(detailed_results) > 1 else 0,
                     'overhead_is_constant': (statistics.stdev([r['estimated_overhead'] for r in detailed_results]) < statistics.mean([r['estimated_overhead'] for r in detailed_results]) * 0.1) if len(detailed_results) >= 2 else False
                 }
            }
        }
    
    def save_results(self, results: Dict, test_name: str):
        """Sauvegarde les résultats dans des fichiers CSV et JSON"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        results_dir = os.path.join(os.path.dirname(__file__), "results")
        os.makedirs(results_dir, exist_ok=True)
        
        # Sauvegarde JSON
        json_path = os.path.join(results_dir, f"{timestamp}_benchmark_serialcomm_{test_name}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            # Convertir les numpy arrays en listes pour la sérialisation JSON
            json_results = self._prepare_for_json(results)
            json.dump(json_results, f, indent=2)
        
        print(f"📄 Résultats sauvegardés: {json_path}")
        return json_path
    
    def _prepare_for_json(self, obj):
        """Prépare les données pour la sérialisation JSON"""
        if isinstance(obj, dict):
            return {k: self._prepare_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._prepare_for_json(item) for item in obj]
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, (np.int64, np.int32)):
            return int(obj)
        else:
            return obj
    
    def generate_plots(self, results: Dict, test_name: str):
        """Génère des graphiques pour visualiser les résultats"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        results_dir = os.path.join(os.path.dirname(__file__), "results")
        os.makedirs(results_dir, exist_ok=True)
        
        if test_name == "latency" and 'latencies' in results and 'min_latency' in results:
            self._plot_latency_distribution(results, timestamp)
        elif test_name == "sweep" and 'sweep_results' in results:
            self._plot_m_value_sweep(results, timestamp)
        elif test_name == "acquisition_comparison" and isinstance(results, dict):
            self._plot_acquisition_comparison(results, timestamp)
        elif test_name == "sweep_detailed" and 'detailed_results' in results:
            self._plot_sweep_detailed(results, timestamp)
        # Pas de génération de graphiques pour les autres cas pour éviter les erreurs
    
    def _plot_latency_distribution(self, results: Dict, timestamp: str):
        """Graphique de distribution des latences"""
        plt.figure(figsize=(12, 8))
        
        # Histogramme des latences
        plt.subplot(2, 2, 1)
        plt.hist(results['latencies'], bins=50, alpha=0.7, color='blue')
        plt.title(f'Distribution des latences (m={results["m_value"]})')
        plt.xlabel('Latence (ms)')
        plt.ylabel('Fréquence')
        plt.grid(True)
        
        # Évolution des latences
        plt.subplot(2, 2, 2)
        plt.plot(results['latencies'], alpha=0.7)
        plt.title(f'Évolution des latences (m={results["m_value"]})')
        plt.xlabel('Numéro de test')
        plt.ylabel('Latence (ms)')
        plt.grid(True)
        
        # Statistiques
        plt.subplot(2, 2, 3)
        stats = ['Moyenne', 'Min', 'Max', 'Écart-type']
        values = [results['mean_latency'], results['min_latency'], 
                 results['max_latency'], results['std_latency']]
        plt.bar(stats, values, color=['blue', 'green', 'red', 'orange'])
        plt.title(f'Statistiques des latences (m={results["m_value"]})')
        plt.ylabel('Latence (ms)')
        plt.grid(True)
        
        # Taux de succès
        plt.subplot(2, 2, 4)
        plt.pie([results['successful_tests'], results['total_tests'] - results['successful_tests']], 
                labels=['Succès', 'Échecs'], colors=['green', 'red'], autopct='%1.1f%%')
        plt.title(f'Taux de succès (m={results["m_value"]})')
        
        plt.tight_layout()
        fig_path = os.path.join(os.path.dirname(__file__), "results", 
                               f"{timestamp}_benchmark_latency_m{results['m_value']}.png")
        plt.savefig(fig_path)
        plt.close()
        print(f"📊 Graphique latence sauvegardé: {fig_path}")
    
    def _plot_m_value_sweep(self, results: Dict, timestamp: str):
        """Graphique du sweep des facteurs de moyennage"""
        sweep_data = results['sweep_results']
        m_values = [r['m_value'] for r in sweep_data]
        throughputs = [r['throughput'] for r in sweep_data]
        latencies = [r['mean_latency'] for r in sweep_data]
        
        plt.figure(figsize=(12, 8))
        
        # Débit vs facteur de moyennage
        plt.subplot(2, 2, 1)
        plt.plot(m_values, throughputs, 'bo-', linewidth=2, markersize=8)
        plt.title('Débit vs Facteur de moyennage')
        plt.xlabel('Facteur de moyennage (m)')
        plt.ylabel('Débit (acquisitions/s)')
        plt.grid(True)
        plt.yscale('log')
        
        # Latence vs facteur de moyennage
        plt.subplot(2, 2, 2)
        plt.plot(m_values, latencies, 'ro-', linewidth=2, markersize=8)
        plt.title('Latence vs Facteur de moyennage')
        plt.xlabel('Facteur de moyennage (m)')
        plt.ylabel('Latence moyenne (ms)')
        plt.grid(True)
        
        # Taux de succès
        plt.subplot(2, 2, 3)
        success_rates = [r['success_rate'] for r in sweep_data]
        plt.plot(m_values, success_rates, 'go-', linewidth=2, markersize=8)
        plt.title('Taux de succès vs Facteur de moyennage')
        plt.xlabel('Facteur de moyennage (m)')
        plt.ylabel('Taux de succès (%)')
        plt.ylim(95, 101)
        plt.grid(True)
        
        # Nombre d'acquisitions par test
        plt.subplot(2, 2, 4)
        acq_counts = [r['successful_acq'] for r in sweep_data]
        plt.bar(range(len(m_values)), acq_counts, color='purple', alpha=0.7)
        plt.title('Acquisitions réussies par test')
        plt.xlabel('Index du test')
        plt.ylabel('Nombre d\'acquisitions')
        plt.xticks(range(len(m_values)), m_values)
        plt.grid(True)
        
        plt.tight_layout()
        fig_path = os.path.join(os.path.dirname(__file__), "results", 
                               f"{timestamp}_benchmark_sweep_moyennage.png")
        plt.savefig(fig_path)
        plt.close()
        print(f"📊 Graphique sweep sauvegardé: {fig_path}")
    
    def _plot_acquisition_comparison(self, results: Dict, timestamp: str):
        """Graphique de comparaison des méthodes d'acquisition"""
        # Implémentation de la génération du graphique de comparaison
        pass
    
    def _plot_sweep_detailed(self, results: Dict, timestamp: str):
        """Graphique détaillé du sweep des facteurs de moyennage"""
        detailed_data = results['detailed_results']
        m_values = [r['m_value'] for r in detailed_data]
        throughputs = [r['throughput'] for r in detailed_data]
        latencies = [r['mean_latency'] for r in detailed_data]
        theoretical_times = [r['theoretical_acq_time'] for r in detailed_data]
        overheads = [r['estimated_overhead'] for r in detailed_data]
        
        plt.figure(figsize=(15, 10))
        
        # Débit vs facteur de moyennage
        plt.subplot(2, 3, 1)
        plt.plot(m_values, throughputs, 'bo-', linewidth=2, markersize=8)
        plt.title('Débit vs Facteur de moyennage')
        plt.xlabel('Facteur de moyennage (m)')
        plt.ylabel('Débit (acquisitions/s)')
        plt.grid(True)
        plt.yscale('log')
        
        # Latence vs facteur de moyennage
        plt.subplot(2, 3, 2)
        plt.plot(m_values, latencies, 'ro-', linewidth=2, markersize=8, label='Latence mesurée')
        plt.plot(m_values, theoretical_times, 'g--', linewidth=2, markersize=6, label='Temps théorique')
        plt.title('Latence vs Facteur de moyennage')
        plt.xlabel('Facteur de moyennage (m)')
        plt.ylabel('Latence (ms)')
        plt.grid(True)
        plt.legend()
        
        # Overhead vs facteur de moyennage
        plt.subplot(2, 3, 3)
        plt.plot(m_values, overheads, 'mo-', linewidth=2, markersize=8)
        plt.title('Overhead de communication')
        plt.xlabel('Facteur de moyennage (m)')
        plt.ylabel('Overhead (ms)')
        plt.grid(True)
        
        # Efficacité (temps théorique / temps mesuré)
        plt.subplot(2, 3, 4)
        efficiencies = [(theo/mes)*100 for theo, mes in zip(theoretical_times, latencies)]
        plt.plot(m_values, efficiencies, 'co-', linewidth=2, markersize=8)
        plt.title('Efficacité de l\'acquisition')
        plt.xlabel('Facteur de moyennage (m)')
        plt.ylabel('Efficacité (%)')
        plt.grid(True)
        
        # Distribution des latences pour m=127
        plt.subplot(2, 3, 5)
        m127_data = next((r for r in detailed_data if r['m_value'] == 127), None)
        if m127_data and 'individual_latencies' in m127_data:
            plt.hist(m127_data['individual_latencies'], bins=20, alpha=0.7, color='orange')
            plt.title('Distribution latences (m=127)')
            plt.xlabel('Latence (ms)')
            plt.ylabel('Fréquence')
            plt.grid(True)
        
        # Résumé des statistiques
        plt.subplot(2, 3, 6)
        plt.axis('off')
        stats_text = f"""Statistiques détaillées:
        
• Plage facteurs: {min(m_values)} à {max(m_values)}
• Débit max: {max(throughputs):.2f} acq/s (m={m_values[throughputs.index(max(throughputs))]})
• Débit min: {min(throughputs):.2f} acq/s (m={m_values[throughputs.index(min(throughputs))]})
• Overhead moyen: {np.mean(overheads):.2f} ± {np.std(overheads):.2f} ms
• Efficacité moyenne: {np.mean(efficiencies):.1f}%

Analyse overhead:
{'• Overhead constant' if results['analysis']['overhead_analysis']['overhead_is_constant'] else '• Overhead variable'}
        """
        plt.text(0.1, 0.9, stats_text, transform=plt.gca().transAxes, 
                fontsize=10, verticalalignment='top', fontfamily='monospace')
        
        plt.tight_layout()
        fig_path = os.path.join(os.path.dirname(__file__), "results", 
                               f"{timestamp}_benchmark_sweep_detaille_moyennage.png")
        plt.savefig(fig_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"📊 Graphique détaillé sauvegardé: {fig_path}")
    
    def run_complete_benchmark(self):
        """Exécute une suite complète de benchmarks"""
        print("🚀 BENCHMARK COMPLET DE SERIALCOMMUNICATOR")
        print("=" * 50)
        
        if not self.connect():
            return False
        
        try:
            # 1. Test de latence
            latency_results = self.benchmark_acquisition_latency(m_value=127, num_tests=100)
            if latency_results:
                self.save_results(latency_results, "latency")
                self.generate_plots(latency_results, "latency")
            
            # 2. Test de débit
            throughput_results = self.benchmark_acquisition_throughput(m_value=127, duration=10.0)
            if throughput_results:
                self.save_results(throughput_results, "throughput")
                self.generate_plots(throughput_results, "throughput")
            
            # 3. Test de configuration
            config_results = self.benchmark_configuration_speed(num_tests=50)
            if config_results:
                self.save_results(config_results, "configuration")
                self.generate_plots(config_results, "configuration")
            
            # 4. Sweep facteur de moyennage
            sweep_results = self.benchmark_m_value_sweep(duration=5.0)
            if sweep_results:
                self.save_results(sweep_results, "sweep")
                self.generate_plots(sweep_results, "sweep")
            
            # 5. Test avec délai entre commandes
            delay_results = self.benchmark_m_value_with_delay(duration=5.0, delay_ms=10.0)
            if delay_results:
                self.save_results(delay_results, "with_delay")
                self.generate_plots(delay_results, "with_delay")
            
            # 6. Analyse décomposition temps
            analysis_results = self.analyze_overhead_vs_acquisition_time()
            if analysis_results:
                self.save_results(analysis_results, "overhead_analysis")
                self.generate_plots(analysis_results, "overhead_analysis")
            
            # 7. Comparaison des méthodes d'acquisition (sans ultra_fast)
            comparison_results = self.compare_acquisition_methods(duration=10.0)
            if comparison_results:
                self.save_results(comparison_results, "acquisition_comparison")
                self.generate_plots(comparison_results, "acquisition_comparison")
            
            # 8. Test de qualité des données
            data_quality_results = self.benchmark_data_quality(m_value=127, num_samples=100)
            if data_quality_results:
                self.save_results(data_quality_results, "data_quality")
                self.generate_plots(data_quality_results, "data_quality")
            
            # 9. Test détaillé sweep facteur de moyennage
            detailed_results = self.benchmark_m_value_sweep_detailed(num_samples=50)
            if detailed_results:
                self.save_results(detailed_results, "sweep_detailed")
                self.generate_plots(detailed_results, "sweep_detailed")
            
            # 10. Test réaliste avec écriture CSV
            print("\n10. Test réaliste avec écriture CSV...")
            realistic_results = self.benchmark_realistic_acquisition_with_csv(m_value=127, duration=60.0)
            if realistic_results:
                self.save_results(realistic_results, "realistic_csv")
                self.generate_plots(realistic_results, "realistic_csv")
                
                # Analyse automatique de la qualité
                quality_results = self.analyze_csv_data_quality(realistic_results['csv_file'])
                if quality_results:
                    self.save_results(quality_results, "csv_quality_analysis")
            
            print("\n✅ BENCHMARK COMPLET TERMINÉ")
            return True
            
        finally:
            self.disconnect()

    @staticmethod
    def validate_acquisition_data(response: str) -> tuple[bool, str]:
        """
        Valide que la réponse d'acquisition contient bien 8 valeurs numériques
        
        Args:
            response: La réponse brute de la carte (ex: "3789\t3181\t3071\t3113\t1666\t1987\t2351\t2212\t")
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not response or response.strip() == "":
            return False, "Réponse vide"
        
        try:
            # Séparer par tabulations ET virgules (pour compatibilité)
            if '\t' in response:
                values = [val.strip() for val in response.split('\t') if val.strip()]
            else:
                values = [val.strip() for val in response.split(',') if val.strip()]
            
            # Vérifier qu'on a exactement 8 valeurs
            if len(values) != 8:
                return False, f"Nombre de valeurs incorrect: {len(values)} au lieu de 8"
            
            # Vérifier que toutes les valeurs sont numériques
            numeric_values = []
            for i, val in enumerate(values):
                try:
                    numeric_val = float(val)
                    numeric_values.append(numeric_val)
                except ValueError:
                    return False, f"Valeur non numérique à l'index {i}: '{val}'"
            
            # Vérifications additionnelles de qualité
            # Vérifier qu'on n'a pas que des zéros (signe d'un problème)
            if all(v == 0.0 for v in numeric_values):
                return False, "Toutes les valeurs sont à zéro (problème potentiel)"
            
            # Vérifier qu'on n'a pas de valeurs aberrantes (par ex. trop grandes)
            max_reasonable_value = 1e6  # Ajustez selon vos spécifications
            if any(abs(v) > max_reasonable_value for v in numeric_values):
                return False, f"Valeurs aberrantes détectées (> {max_reasonable_value})"
            
            return True, f"8 valeurs valides: {numeric_values}"
            
        except Exception as e:
            return False, f"Erreur de parsing: {str(e)}"

    def benchmark_realistic_acquisition_with_csv(self, m_value: int = 127, duration: float = 30.0, csv_filename: str = None) -> Dict:
        """
        Benchmark réaliste avec écriture CSV complète et validation des données
        Mesure le temps total : acquisition + parsing + écriture + flush
        """
        from datetime import datetime
        import csv
        
        if csv_filename is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
            csv_filename = f"{timestamp}_benchmark_realistic_m{m_value}_acquisition_data.csv"
        
        results_dir = os.path.join(os.path.dirname(__file__), "results")
        os.makedirs(results_dir, exist_ok=True)
        csv_path = os.path.join(results_dir, csv_filename)
        
        print(f"\n🎯 Benchmark réaliste avec CSV (m={m_value}, {duration}s)")
        print(f"   Fichier: {csv_filename}")
        
        # Statistiques de performance
        latencies_total = []          # Temps total (acquisition + écriture)
        latencies_acquisition = []    # Temps acquisition seule
        latencies_processing = []     # Temps traitement + écriture
        successful_acq = 0
        total_acq = 0
        corrupted_data = 0
        
        # Validation des données
        validation_errors = []
        data_samples = []
        
        start_time = time.time()
        
        # Ouvrir le fichier CSV
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                # En-tête CSV avec métadonnées
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow([
                    'timestamp', 'acquisition_id', 'm_value', 
                    'adc1_ch1', 'adc1_ch2', 'adc1_ch3', 'adc1_ch4',
                    'adc2_ch1', 'adc2_ch2', 'adc2_ch3', 'adc2_ch4',
                    'acquisition_time_ms', 'is_valid'
                ])
                
                while (time.time() - start_time) < duration:
                    # Temps total début
                    total_start = time.perf_counter()
                    
                    # 1. ACQUISITION
                    acq_start = time.perf_counter()
                    cmd = f"m{m_value}"
                    success, response = self.comm.send_command(cmd)
                    acq_end = time.perf_counter()
                    
                    # 2. TRAITEMENT ET ÉCRITURE
                    processing_start = time.perf_counter()
                    
                    total_acq += 1
                    acquisition_time = (acq_end - acq_start) * 1000  # ms
                    
                    if success and response:
                        # Validation et parsing des données
                        is_valid, validation_msg = self.validate_acquisition_data(response)
                        
                        if is_valid:
                            successful_acq += 1
                            
                            # Parser les 8 valeurs
                            try:
                                if '\t' in response:
                                    values = [val.strip() for val in response.split('\t') if val.strip()]
                                else:
                                    values = [val.strip() for val in response.split(',') if val.strip()]
                                
                                # Convertir en float pour validation supplémentaire
                                numeric_values = [float(val) for val in values[:8]]
                                
                                # Timestamp précis
                                timestamp = datetime.now().isoformat()
                                
                                # Écrire dans le CSV
                                csvwriter.writerow([
                                    timestamp, total_acq, m_value,
                                    *numeric_values,  # Les 8 valeurs ADC
                                    acquisition_time, True
                                ])
                                
                                # Garder quelques échantillons pour analyse
                                if len(data_samples) < 10:
                                    data_samples.append({
                                        'timestamp': timestamp,
                                        'values': numeric_values,
                                        'acquisition_time': acquisition_time,
                                        'raw_response': response
                                    })
                                
                            except (ValueError, IndexError) as e:
                                corrupted_data += 1
                                # Enregistrer même les données corrompues pour analyse
                                timestamp = datetime.now().isoformat()
                                csvwriter.writerow([
                                    timestamp, total_acq, m_value,
                                    '', '', '', '', '', '', '', '',  # Valeurs vides
                                    acquisition_time, False
                                ])
                                
                                if len(validation_errors) < 5:
                                    validation_errors.append({
                                        'acquisition_id': total_acq,
                                        'error': str(e),
                                        'response': response[:100]
                                    })
                        else:
                            corrupted_data += 1
                            # Enregistrer l'échec
                            timestamp = datetime.now().isoformat()
                            csvwriter.writerow([
                                timestamp, total_acq, m_value,
                                '', '', '', '', '', '', '', '',
                                acquisition_time, False
                            ])
                            
                            if len(validation_errors) < 5:
                                validation_errors.append({
                                    'acquisition_id': total_acq,
                                    'error': validation_msg,
                                    'response': response[:100]
                                })
                    else:
                        # Échec de communication
                        timestamp = datetime.now().isoformat()
                        csvwriter.writerow([
                            timestamp, total_acq, m_value,
                            '', '', '', '', '', '', '', '',
                            0, False
                        ])
                    
                    processing_end = time.perf_counter()
                    total_end = time.perf_counter()
                    
                    # Mesures de temps
                    latencies_acquisition.append(acquisition_time)
                    processing_time = (processing_end - processing_start) * 1000
                    latencies_processing.append(processing_time)
                    total_time = (total_end - total_start) * 1000
                    latencies_total.append(total_time)
                    
                    # Flush périodique pour s'assurer que les données sont écrites
                    if total_acq % 10 == 0:
                        csvfile.flush()
                        os.fsync(csvfile.fileno())
                    
                    # Affichage du progrès
                    if total_acq % 50 == 0:
                        print(f"   Progrès: {total_acq} acquisitions, {successful_acq} valides ({(successful_acq/total_acq)*100:.1f}%)")
                
                # Flush final
                csvfile.flush()
                os.fsync(csvfile.fileno())
        
        except Exception as e:
            print(f"❌ Erreur lors de l'écriture CSV: {e}")
            return None
        
        elapsed_time = time.time() - start_time
        
        # Calculs de performance
        if latencies_total:
            results = {
                # Métriques de base
                'total_acquisitions': total_acq,
                'successful_acquisitions': successful_acq,
                'corrupted_data': corrupted_data,
                'success_rate': (successful_acq / total_acq) * 100 if total_acq > 0 else 0,
                'elapsed_time': elapsed_time,
                'm_value': m_value,
                
                # Temps d'acquisition
                'acquisition_times': {
                    'mean': statistics.mean(latencies_acquisition),
                    'min': min(latencies_acquisition),
                    'max': max(latencies_acquisition),
                    'std': statistics.stdev(latencies_acquisition) if len(latencies_acquisition) > 1 else 0
                },
                
                # Temps de traitement/écriture
                'processing_times': {
                    'mean': statistics.mean(latencies_processing),
                    'min': min(latencies_processing),
                    'max': max(latencies_processing),
                    'std': statistics.stdev(latencies_processing) if len(latencies_processing) > 1 else 0
                },
                
                # Temps total
                'total_times': {
                    'mean': statistics.mean(latencies_total),
                    'min': min(latencies_total),
                    'max': max(latencies_total),
                    'std': statistics.stdev(latencies_total) if len(latencies_total) > 1 else 0
                },
                
                # Débits
                'throughput_total': successful_acq / elapsed_time,
                'theoretical_max_throughput': 1000 / statistics.mean(latencies_total) if latencies_total else 0,
                
                # Fichier et validation
                'csv_file': csv_path,
                'csv_size_bytes': os.path.getsize(csv_path),
                'validation_errors': validation_errors,
                'data_samples': data_samples,
                
                # Overhead
                'overhead_percentage': (statistics.mean(latencies_processing) / statistics.mean(latencies_total)) * 100 if latencies_total else 0
            }
            
            # Affichage des résultats
            print(f"\n=== RÉSULTATS BENCHMARK RÉALISTE ===")
            print(f"📊 Acquisitions: {successful_acq}/{total_acq} valides ({results['success_rate']:.1f}%)")
            print(f"🚀 Débit réel: {results['throughput_total']:.2f} acq/s")
            print(f"⏱️ Temps moyen total: {results['total_times']['mean']:.2f}ms")
            print(f"   - Acquisition: {results['acquisition_times']['mean']:.2f}ms")
            print(f"   - Traitement+CSV: {results['processing_times']['mean']:.2f}ms")
            print(f"💾 Fichier CSV: {csv_filename} ({results['csv_size_bytes']} bytes)")
            print(f"⚙️ Overhead traitement: {results['overhead_percentage']:.1f}%")
            
            if corrupted_data > 0:
                print(f"⚠️ Données corrompues: {corrupted_data} ({(corrupted_data/total_acq)*100:.1f}%)")
            
            if validation_errors:
                print(f"🔍 Premières erreurs de validation:")
                for error in validation_errors[:3]:
                    print(f"   Acq #{error['acquisition_id']}: {error['error']}")
            
            return results
        else:
            print("❌ Aucune donnée collectée")
            return None
    
    def analyze_csv_data_quality(self, csv_path: str) -> Dict:
        """
        Analyse a posteriori de la qualité des données dans un fichier CSV de benchmark
        """
        import pandas as pd
        
        print(f"\n🔬 Analyse qualité des données: {os.path.basename(csv_path)}")
        
        try:
            # Charger les données
            df = pd.read_csv(csv_path)
            
            # Statistiques de base
            total_rows = len(df)
            valid_rows = df['is_valid'].sum()
            invalid_rows = total_rows - valid_rows
            
            print(f"📊 Données totales: {total_rows}")
            print(f"✅ Données valides: {valid_rows} ({(valid_rows/total_rows)*100:.1f}%)")
            print(f"❌ Données invalides: {invalid_rows} ({(invalid_rows/total_rows)*100:.1f}%)")
            
            if valid_rows > 0:
                # Analyse des données valides seulement
                valid_df = df[df['is_valid'] == True]
                
                # Statistiques des temps d'acquisition
                acq_times = valid_df['acquisition_time_ms']
                print(f"\n⏱️ Temps d'acquisition (ms):")
                print(f"   Moyenne: {acq_times.mean():.2f} ± {acq_times.std():.2f}")
                print(f"   Min/Max: {acq_times.min():.2f} / {acq_times.max():.2f}")
                
                # Analyse des valeurs ADC
                adc_columns = [f'adc{i}_ch{j}' for i in [1,2] for j in [1,2,3,4]]
                adc_data = valid_df[adc_columns]
                
                print(f"\n📈 Données ADC:")
                print(f"   Valeurs nulles détectées: {adc_data.isnull().sum().sum()}")
                print(f"   Plage globale: {adc_data.min().min():.1f} à {adc_data.max().max():.1f}")
                
                # Détection d'anomalies
                anomalies = []
                
                # 1. Valeurs identiques consécutives (possible duplication)
                for col in adc_columns:
                    consecutive_same = (adc_data[col] == adc_data[col].shift(1)).sum()
                    if consecutive_same > valid_rows * 0.1:  # Plus de 10% de valeurs identiques consécutives
                        anomalies.append(f"Valeurs consécutives identiques en {col}: {consecutive_same}")
                
                # 2. Valeurs aberrantes (au-delà de 3 sigma)
                for col in adc_columns:
                    mean_val = adc_data[col].mean()
                    std_val = adc_data[col].std()
                    outliers = ((adc_data[col] - mean_val).abs() > 3 * std_val).sum()
                    if outliers > 0:
                        anomalies.append(f"Valeurs aberrantes en {col}: {outliers}")
                
                if anomalies:
                    print(f"\n⚠️ Anomalies détectées:")
                    for anomaly in anomalies:
                        print(f"   {anomaly}")
                else:
                    print(f"\n✅ Aucune anomalie majeure détectée")
            
            return {
                'total_rows': total_rows,
                'valid_rows': valid_rows,
                'invalid_rows': invalid_rows,
                'validity_rate': (valid_rows/total_rows)*100,
                'csv_path': csv_path,
                'file_size': os.path.getsize(csv_path),
                'anomalies': anomalies if 'anomalies' in locals() else []
            }
            
        except Exception as e:
            print(f"❌ Erreur lors de l'analyse: {e}")
            return None

if __name__ == "__main__":
    # Configuration
    PORT = "COM10"  # À adapter selon votre configuration
    BAUD = 1500000

    benchmark = SerialCommunicatorBenchmark(PORT, BAUD)

    print("🔧 BENCHMARK SERIALCOMMUNICATOR")
    print("Choisissez le type de test :")
    print("1. Test latence d'acquisition (m=127, 100 tests)")
    print("2. Test débit d'acquisition (m=127, 10s)")
    print("3. Test vitesse de configuration")
    print("4. Sweep facteur de moyennage")
    print("5. Test avec délai entre commandes")
    print("6. Analyse décomposition temps")
    print("7. Comparaison des méthodes d'acquisition")
    print("8. Test qualité des données")
    print("9. Benchmark complet (tous les tests)")
    print("10. Détecter les ports série disponibles")
    print("11. 🔬 Sweep détaillé facteur de moyennage (RECOMMANDÉ)")
    print("12. 🎯 Test réaliste avec écriture CSV (PRODUCTION)")
    print("13. 📊 Analyser qualité données d'un fichier CSV")
    
    choix = input("Votre choix (1-13) : ").strip()

    if choix == "1":
        m_value = int(input("Facteur de moyennage (ex: 127) : ") or "127")
        num_tests = int(input("Nombre de tests (ex: 100) : ") or "100")
        
        if benchmark.connect():
            try:
                results = benchmark.benchmark_acquisition_latency(m_value, num_tests)
                if results:
                    benchmark.save_results(results, "latency")
                    benchmark.generate_plots(results, "latency")
            finally:
                benchmark.disconnect()
                
    elif choix == "2":
        m_value = int(input("Facteur de moyennage (ex: 127) : ") or "127")
        duration = float(input("Durée du test (ex: 10.0) : ") or "10.0")
        
        if benchmark.connect():
            try:
                results = benchmark.benchmark_acquisition_throughput(m_value, duration)
                if results:
                    benchmark.save_results(results, "throughput")
                    benchmark.generate_plots(results, "throughput")
            finally:
                benchmark.disconnect()
                
    elif choix == "3":
        num_tests = int(input("Nombre de tests par configuration (ex: 50) : ") or "50")
        
        if benchmark.connect():
            try:
                results = benchmark.benchmark_configuration_speed(num_tests)
                if results:
                    benchmark.save_results(results, "configuration")
                    benchmark.generate_plots(results, "configuration")
            finally:
                benchmark.disconnect()
                
    elif choix == "4":
        duration = float(input("Durée par test (ex: 5.0) : ") or "5.0")
        
        if benchmark.connect():
            try:
                results = benchmark.benchmark_m_value_sweep(duration=duration)
                if results:
                    benchmark.save_results(results, "sweep")
                    benchmark.generate_plots(results, "sweep")
            finally:
                benchmark.disconnect()
                
    elif choix == "5":
        duration = float(input("Durée par test (ex: 5.0) : ") or "5.0")
        delay_ms = float(input("Délai entre commandes (ex: 10.0) : ") or "10.0")
        
        if benchmark.connect():
            try:
                results = benchmark.benchmark_m_value_with_delay(duration=duration, delay_ms=delay_ms)
                if results:
                    benchmark.save_results(results, "with_delay")
                    benchmark.generate_plots(results, "with_delay")
            finally:
                benchmark.disconnect()
                
    elif choix == "6":
        if benchmark.connect():
            try:
                results = benchmark.analyze_overhead_vs_acquisition_time()
                if results:
                    benchmark.save_results(results, "overhead_analysis")
                    benchmark.generate_plots(results, "overhead_analysis")
            finally:
                benchmark.disconnect()
                
    elif choix == "7":
        # La connexion est maintenant gérée automatiquement dans compare_acquisition_methods
        results = benchmark.compare_acquisition_methods(duration=10.0)
        if results:
            benchmark.save_results(results, "acquisition_comparison")
            benchmark.generate_plots(results, "acquisition_comparison")
                
    elif choix == "8":
        m_value = int(input("Facteur de moyennage (ex: 127) : ") or "127")
        num_samples = int(input("Nombre d'échantillons (ex: 100) : ") or "100")
        
        if benchmark.connect():
            try:
                results = benchmark.benchmark_data_quality(m_value=m_value, num_samples=num_samples)
                if results:
                    benchmark.save_results(results, "data_quality")
                    benchmark.generate_plots(results, "data_quality")
            finally:
                benchmark.disconnect()
                
    elif choix == "9":
        benchmark.run_complete_benchmark()
        
    elif choix == "10":
        available_ports = benchmark.detect_available_ports()
        print("📡 Ports série disponibles:")
        for i, port in enumerate(available_ports):
            print(f"   {i+1}. {port['device']} - {port['description']} ({port['manufacturer']})")
            
    elif choix == "11":
        num_samples = int(input("Nombre d'échantillons par test (ex: 50) : ") or "50")
        
        if benchmark.connect():
            try:
                results = benchmark.benchmark_m_value_sweep_detailed(num_samples=num_samples)
                if results:
                    benchmark.save_results(results, "sweep_detailed")
                    benchmark.generate_plots(results, "sweep_detailed")
            finally:
                benchmark.disconnect()
                
    elif choix == "12":
        m_value = int(input("Facteur de moyennage (ex: 127) : ") or "127")
        duration = float(input("Durée du test en secondes (ex: 30.0) : ") or "30.0")
        csv_filename = input("Nom du fichier CSV (laisser vide pour auto) : ").strip() or None
        
        if benchmark.connect():
            try:
                results = benchmark.benchmark_realistic_acquisition_with_csv(
                    m_value=m_value, 
                    duration=duration, 
                    csv_filename=csv_filename
                )
                if results:
                    benchmark.save_results(results, "realistic_csv")
                    benchmark.generate_plots(results, "realistic_csv")
                    
                    # Proposer l'analyse automatique
                    analyze = input("\n🔍 Analyser la qualité des données maintenant ? (o/n) : ").strip().lower()
                    if analyze in ['o', 'oui', 'y', 'yes']:
                        quality_results = benchmark.analyze_csv_data_quality(results['csv_file'])
                        if quality_results:
                            benchmark.save_results(quality_results, "csv_quality_analysis")
            finally:
                benchmark.disconnect()
                
    elif choix == "13":
        csv_path = input("Chemin vers le fichier CSV à analyser : ").strip()
        if os.path.exists(csv_path):
            quality_results = benchmark.analyze_csv_data_quality(csv_path)
            if quality_results:
                benchmark.save_results(quality_results, "csv_quality_analysis")
        else:
            print(f"❌ Fichier non trouvé: {csv_path}")
        
    else:
        print("Choix non reconnu. Arrêt.")
