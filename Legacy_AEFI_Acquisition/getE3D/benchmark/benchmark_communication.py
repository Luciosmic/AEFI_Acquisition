#!/usr/bin/env python3
"""
Module de benchmark pour la communication série avec la carte DDS/ADC
"""

import time
import statistics
from typing import List, Tuple
import serial
import threading
from queue import Queue
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import os
import json
import csv
import sys

# Ajouter le chemin vers les instruments
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "instruments"))
from AD9106_ADS131A04_SerialCommunicationModule import SerialCommunicator

class CommunicationBenchmark:
    def __init__(self, port: str, baudrate: int = 1500000, quick_test: bool = False):
        self.port = port
        self.baudrate = baudrate
        self.quick_test = quick_test
        self.ser = None
        self.results = {
            'latency': [],
            'throughput': [],
            'stability': []
        }
        
    def connect(self) -> bool:
        """Établit la connexion série"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=8,
                stopbits=serial.STOPBITS_ONE,
                parity=serial.PARITY_NONE,
                timeout=2
            )
            return True
        except Exception as e:
            print(f"Erreur de connexion: {str(e)}")
            return False
            
    def disconnect(self):
        """Ferme la connexion série"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            
    def measure_command_latency(self, num_commands: int = 100) -> List[float]:
        """Mesure la latence pour l'envoi d'une commande simple"""
        latencies = []
        
        for _ in range(num_commands):
            start_time = time.perf_counter()
            self.ser.write(b'a13*')  # Commande simple pour sélectionner l'adresse 13
            self.ser.readline()  # Lire la réponse
            end_time = time.perf_counter()
            
            latency = (end_time - start_time) * 1000  # Convertir en ms
            latencies.append(latency)
            
        return latencies
        
    def measure_throughput(self, duration: float = 10.0) -> Tuple[int, float]:
        """Mesure le nombre de commandes pouvant être envoyées par seconde"""
        start_time = time.time()
        command_count = 0
        
        while (time.time() - start_time) < duration:
            self.ser.write(b'a13*')
            self.ser.readline()
            command_count += 1
            
        elapsed_time = time.time() - start_time
        throughput = command_count / elapsed_time
        
        return command_count, throughput
        
    def test_stability(self, duration: float = 3600) -> List[float]:
        """Test de stabilité sur une longue durée"""
        latencies = []
        start_time = time.time()
        
        while (time.time() - start_time) < duration:
            latency = self.measure_command_latency(1)[0]
            latencies.append(latency)
            
        return latencies
        
    def save_results_json(self):
        """Sauvegarde les paramètres et résultats dans un fichier JSON dans le dossier results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mode = "quick" if self.quick_test else "full"
        results_dir = os.path.join(os.path.dirname(__file__), "results")
        os.makedirs(results_dir, exist_ok=True)
        data = {
            "timestamp": timestamp,
            "mode": mode,
            "port": self.port,
            "baudrate": self.baudrate,
            "latency": {
                "values": self.results['latency'],
                "mean": float(np.mean(self.results['latency'])) if self.results['latency'] else None,
                "min": float(np.min(self.results['latency'])) if self.results['latency'] else None,
                "max": float(np.max(self.results['latency'])) if self.results['latency'] else None,
                "std": float(np.std(self.results['latency'])) if self.results['latency'] else None
            },
            "throughput": {
                "values": self.results['throughput'],
                "mean": float(np.mean(self.results['throughput'])) if self.results['throughput'] else None
            },
            "stability": {
                "values": self.results['stability'],
                "mean": float(np.mean(self.results['stability'])) if self.results['stability'] else None,
                "std": float(np.std(self.results['stability'])) if self.results['stability'] else None,
                "count": len(self.results['stability'])
            }
        }
        json_path = os.path.join(results_dir, f"benchmark_results_{mode}_{timestamp}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Résultats sauvegardés dans {json_path}")
        
    def run_all_benchmarks(self):
        """Exécute tous les benchmarks et génère un rapport"""
        print("Démarrage des benchmarks...")
        
        # Test de latence
        print("\n1. Test de latence...")
        latencies = self.measure_command_latency()
        self.results['latency'] = latencies
        print(f"Latence moyenne: {statistics.mean(latencies):.2f} ms")
        print(f"Latence min: {min(latencies):.2f} ms")
        print(f"Latence max: {max(latencies):.2f} ms")
        print(f"Écart-type: {statistics.stdev(latencies):.2f} ms")
        
        # Test de débit
        print("\n2. Test de débit...")
        count, throughput = self.measure_throughput()
        self.results['throughput'] = [throughput]
        print(f"Commandes envoyées: {count}")
        print(f"Débit: {throughput:.2f} commandes/seconde")
        
        # Test de stabilité
        print("\n3. Test de stabilité...")
        stability_duration = 30 if self.quick_test else 3600  # 10 minute en mode rapide, 1 heure en mode normal
        print(f"Durée du test: {stability_duration} secondes")
        stability_data = self.test_stability(stability_duration)
        self.results['stability'] = stability_data
        print(f"Nombre de mesures: {len(stability_data)}")
        print(f"Latence moyenne: {statistics.mean(stability_data):.2f} ms")
        print(f"Écart-type: {statistics.stdev(stability_data):.2f} ms")
        
        # Génération des graphiques
        self.generate_plots()
        # Sauvegarde des résultats JSON
        self.save_results_json()
        
    def generate_plots(self):
        """Génère des graphiques pour visualiser les résultats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mode = "quick" if self.quick_test else "full"
        results_dir = os.path.join(os.path.dirname(__file__), "results")
        os.makedirs(results_dir, exist_ok=True)
        
        # Graphique de latence
        plt.figure(figsize=(10, 6))
        plt.hist(self.results['latency'], bins=50)
        plt.title('Distribution de la Latence')
        plt.xlabel('Latence (ms)')
        plt.ylabel('Fréquence')
        plt.savefig(os.path.join(results_dir, f'latency_hist_{mode}_{timestamp}.png'))
        
        # Graphique de stabilité
        plt.figure(figsize=(10, 6))
        plt.plot(self.results['stability'])
        plt.title(f'Stabilité de la Latence ({mode} test)')
        plt.xlabel('Temps (s)')
        plt.ylabel('Latence (ms)')
        plt.savefig(os.path.join(results_dir, f'stability_plot_{mode}_{timestamp}.png'))
        
        plt.close('all')

    def run_acquisition_benchmark_sync(self, m_value=32, duration=10.0):
        """Benchmark acquisition réelle synchrone avec commande mXX*
        
        Mesure trois aspects de la performance :
        1. Latence : temps entre l'envoi de la commande et la réception de la réponse
        2. Débit : nombre d'acquisitions par seconde
        3. Stabilité : variation de la latence dans le temps
        """
        ser = serial.Serial(self.port, self.baudrate, timeout=2)
        start_time = time.time()
        latencies = []
        count = 0
        responses = 0
        
        while (time.time() - start_time) < duration:
            cmd = f"m{m_value}*"
            cmd_start = time.perf_counter()
            ser.write(cmd.encode())
            resp = ser.readline().decode().strip()
            cmd_end = time.perf_counter()
            
            count += 1
            if resp:
                responses += 1
                latency = (cmd_end - cmd_start) * 1000  # Conversion en ms
                latencies.append(latency)
            else:
                print("Timeout sur la réponse acquisition (synchrone)")
        
        ser.close()
        elapsed_time = time.time() - start_time
        
        if latencies:
            # Calcul des statistiques de latence
            mean_latency = sum(latencies) / len(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            std_latency = statistics.stdev(latencies) if len(latencies) > 1 else 0
            
            # Calcul du débit
            throughput = responses / elapsed_time
            success_rate = (responses / count) * 100
            
            print(f"\nRésultats pour m={m_value}:")
            print("\n1. Latence:")
            print(f"  - Nombre de mesures: {len(latencies)}")
            print(f"  - Latence moyenne: {mean_latency:.2f} ms")
            print(f"  - Latence min: {min_latency:.2f} ms")
            print(f"  - Latence max: {max_latency:.2f} ms")
            print(f"  - Écart-type: {std_latency:.2f} ms")
            
            print("\n2. Débit:")
            print(f"  - Débit: {throughput:.2f} acquisitions/s")
            print(f"  - Réponses: {responses}/{count} ({success_rate:.1f}%)")
            
            print("\n3. Stabilité:")
            print(f"  - Variation de latence: {max_latency - min_latency:.2f} ms")
            print(f"  - Écart-type: {std_latency:.2f} ms")
            
            # Enregistrement des résultats
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_dir = os.path.join(os.path.dirname(__file__), "results")
            os.makedirs(results_dir, exist_ok=True)
            
            # Sauvegarde des résultats détaillés
            csv_path = os.path.join(results_dir, f"benchmark_m{m_value}_{timestamp}.csv")
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["latency_ms", "timestamp"])
                for i, lat in enumerate(latencies):
                    writer.writerow([lat, i * (elapsed_time / len(latencies))])
            
            # Tracé des graphiques
            plt.figure(figsize=(15, 10))
            
            # 1. Histogramme de latence
            plt.subplot(2, 2, 1)
            plt.hist(latencies, bins=50)
            plt.title(f'Distribution de la Latence (m={m_value})')
            plt.xlabel('Latence (ms)')
            plt.ylabel('Fréquence')
            plt.grid(True)
            
            # 2. Latence dans le temps
            plt.subplot(2, 2, 2)
            plt.plot(range(len(latencies)), latencies)
            plt.title(f'Latence dans le temps (m={m_value})')
            plt.xlabel('Numéro de mesure')
            plt.ylabel('Latence (ms)')
            plt.grid(True)
            
            # 3. Taux de succès
            plt.subplot(2, 2, 3)
            plt.bar(['Succès', 'Échecs'], [responses, count - responses])
            plt.title(f'Taux de succès (m={m_value})')
            plt.ylabel('Nombre de réponses')
            plt.grid(True)
            
            # 4. Débit
            plt.subplot(2, 2, 4)
            plt.bar(['Débit'], [throughput])
            plt.title(f'Débit (m={m_value})')
            plt.ylabel('Acquisitions/s')
            plt.grid(True)
            
            plt.tight_layout()
            fig_path = os.path.join(results_dir, f"benchmark_m{m_value}_{timestamp}.png")
            plt.savefig(fig_path)
            plt.close()
            
            print(f"\nRésultats enregistrés dans {csv_path}")
            print(f"Graphiques enregistrés dans {fig_path}")
            
            return {
                "latencies": latencies,
                "throughput": throughput,
                "success_rate": success_rate,
                "mean_latency": mean_latency,
                "std_latency": std_latency
            }
        else:
            print("Aucune mesure valide obtenue")
            return None

    def sweep_acquisition_benchmark_sync(self, m_values=None, duration=5.0, quick_test=True):
        """Teste le débit pour différents facteurs de moyennage et enregistre les résultats."""
        if m_values is None:
            if quick_test:
                # Points stratégiques pour un test rapide, limité à 127
                m_values = [1, 2, 4, 8, 16, 32, 64, 127]
            else:
                # Test complet jusqu'à 127
                m_values = list(range(1, 128))
            
        print(f"Mode test {'rapide' if quick_test else 'complet'}")
        print(f"Points de test: {m_values}")
        print(f"Durée par point: {duration} secondes")
        results = []
        for m_value in m_values:
            print(f"Test m={m_value}")
            ser = serial.Serial(self.port, self.baudrate, timeout=2)
            start_time = time.time()
            count = 0
            responses = 0
            while (time.time() - start_time) < duration:
                cmd = f"m{m_value}*"
                ser.write(cmd.encode())
                resp = ser.readline().decode().strip()
                count += 1
                if resp:
                    responses += 1
            ser.close()
            elapsed_time = time.time() - start_time
            throughput = responses / elapsed_time
            print(f"m={m_value} : {throughput:.2f} acquisitions/s ({responses}/{count})")
            results.append({
                "m_value": m_value,
                "responses": responses,
                "count": count,
                "throughput": throughput,
                "elapsed_time": elapsed_time
            })
        # Enregistrement CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = os.path.join(os.path.dirname(__file__), "results")
        os.makedirs(results_dir, exist_ok=True)
        csv_path = os.path.join(results_dir, f"sweep_throughput_{timestamp}.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["m_value", "responses", "count", "throughput", "elapsed_time"])
            writer.writeheader()
            writer.writerows(results)
        print(f"Résultats enregistrés dans {csv_path}")
        # Enregistrement paramètres JSON
        params = {
            "timestamp": timestamp,
            "port": self.port,
            "baudrate": self.baudrate,
            "duration": duration,
            "m_values": m_values
        }
        json_path = os.path.join(results_dir, f"sweep_params_{timestamp}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(params, f, indent=2)
        print(f"Paramètres enregistrés dans {json_path}")
        # Tracé figure
        plt.figure(figsize=(10, 6))
        plt.plot([r["m_value"] for r in results], [r["throughput"] for r in results], marker="o")
        plt.xlabel("Facteur de moyennage (m)")
        plt.ylabel("Débit (acquisitions/s)")
        plt.title("Débit en fonction du facteur de moyennage ADC")
        plt.grid(True)
        fig_path = os.path.join(results_dir, f"sweep_throughput_{timestamp}.png")
        plt.savefig(fig_path)
        plt.close()
        print(f"Figure enregistrée dans {fig_path}")

    def test_around_128(self, duration=5.0):
        """Test spécifique autour de la valeur 128 pour démontrer la limite du système.
        
        Ce test montre que le facteur de moyennage ne peut pas dépasser 127.
        Au-delà de 127, le système ignore le moyennage et fonctionne comme si m=1,
        ce qui explique le débit plus élevé observé pour m >= 128.
        
        Les résultats de ce test sont utiles pour :
        1. Démontrer la limite matérielle à 127
        2. Comprendre le comportement du système au-delà de cette limite
        3. Documenter pourquoi il ne faut pas utiliser m > 127
        """
        # Test autour de la limite système (127) et au-delà pour démontrer le changement de comportement
        m_values = list(range(120, 136))
        print("Test autour de la limite système (m=127)")
        print("Ce test démontre que le moyennage ne peut pas dépasser 127")
        print("Au-delà, le système ignore le moyennage et fonctionne comme si m=1")
        print(f"Valeurs testées: {m_values}")
        
        results = []
        for m_value in m_values:
            print(f"\nTest m={m_value}")
            ser = serial.Serial(self.port, self.baudrate, timeout=2)
            start_time = time.time()
            count = 0
            responses = 0
            
            while (time.time() - start_time) < duration:
                cmd = f"m{m_value}*"
                ser.write(cmd.encode())
                resp = ser.readline().decode().strip()
                count += 1
                if resp:
                    responses += 1
            
            ser.close()
            elapsed_time = time.time() - start_time
            throughput = responses / elapsed_time
            print(f"m={m_value}: {throughput:.2f} acquisitions/s ({responses}/{count})")
            
            results.append({
                "m_value": m_value,
                "responses": responses,
                "count": count,
                "throughput": throughput,
                "elapsed_time": elapsed_time
            })
        
        # Enregistrement CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = os.path.join(os.path.dirname(__file__), "results")
        os.makedirs(results_dir, exist_ok=True)
        csv_path = os.path.join(results_dir, f"test_around_128_{timestamp}.csv")
        
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["m_value", "responses", "count", "throughput", "elapsed_time"])
            writer.writeheader()
            writer.writerows(results)
        
        # Tracé simple
        plt.figure(figsize=(10, 6))
        plt.plot([r["m_value"] for r in results], [r["throughput"] for r in results], 'bo-')
        plt.axvline(x=128, color='r', linestyle='--', label='Valeur 128')
        plt.xlabel("Facteur de moyennage (m)")
        plt.ylabel("Débit (acquisitions/s)")
        plt.title("Débit autour de la valeur 128")
        plt.grid(True)
        plt.legend()
        
        fig_path = os.path.join(results_dir, f"test_around_128_{timestamp}.png")
        plt.savefig(fig_path)
        plt.close()
        
        print(f"\nRésultats enregistrés dans {csv_path}")
        print(f"Graphique enregistré dans {fig_path}")
        
        return results

    def benchmark_freq_sweep_sequence(self, duration=10.0, m_value=32):
        """Benchmark la séquence complète : changement de fréquence + acquisition
        
        Mesure le temps nécessaire pour :
        1. Changer la fréquence DDS
        2. Faire une acquisition
        
        Cette mesure est cruciale pour évaluer la performance des sweeps fréquentiels.
        """
        ser = serial.Serial(self.port, self.baudrate, timeout=2)
        start_time = time.time()
        sequences = []
        
        # Fréquence de test (1 kHz)
        test_freq = 1000
        
        while (time.time() - start_time) < duration:
            # 1. Changement de fréquence
            freq_start = time.perf_counter()
            
            # Envoi des commandes de fréquence
            ser.write(f"a62*".encode())  # MSB
            ser.write(f"d8*".encode())
            ser.write(f"a63*".encode())  # LSB
            ser.write(f"d{test_freq & 0xFFFF}*".encode())
            
            # Attendre la fin du changement
            ser.readline()  # Réponse MSB
            ser.readline()  # Réponse LSB
            freq_end = time.perf_counter()
            
            # 2. Acquisition
            acq_start = time.perf_counter()
            ser.write(f"m{m_value}*".encode())
            resp = ser.readline().decode().strip()
            acq_end = time.perf_counter()
            
            if resp:
                freq_time = (freq_end - freq_start) * 1000  # ms
                acq_time = (acq_end - acq_start) * 1000    # ms
                total_time = freq_time + acq_time
                
                sequences.append({
                    "freq_time": freq_time,
                    "acq_time": acq_time,
                    "total_time": total_time
                })
            else:
                print("Timeout sur l'acquisition")
        
        ser.close()
        
        if sequences:
            # Calcul des statistiques
            freq_times = [s["freq_time"] for s in sequences]
            acq_times = [s["acq_time"] for s in sequences]
            total_times = [s["total_time"] for s in sequences]
            
            print(f"\nRésultats du benchmark sweep fréquentiel (m={m_value}):")
            print("\n1. Changement de fréquence:")
            print(f"  - Temps moyen: {statistics.mean(freq_times):.2f} ms")
            print(f"  - Temps min: {min(freq_times):.2f} ms")
            print(f"  - Temps max: {max(freq_times):.2f} ms")
            print(f"  - Écart-type: {statistics.stdev(freq_times):.2f} ms")
            
            print("\n2. Acquisition:")
            print(f"  - Temps moyen: {statistics.mean(acq_times):.2f} ms")
            print(f"  - Temps min: {min(acq_times):.2f} ms")
            print(f"  - Temps max: {max(acq_times):.2f} ms")
            print(f"  - Écart-type: {statistics.stdev(acq_times):.2f} ms")
            
            print("\n3. Séquence complète:")
            print(f"  - Temps moyen: {statistics.mean(total_times):.2f} ms")
            print(f"  - Temps min: {min(total_times):.2f} ms")
            print(f"  - Temps max: {max(total_times):.2f} ms")
            print(f"  - Écart-type: {statistics.stdev(total_times):.2f} ms")
            print(f"  - Débit: {1000/statistics.mean(total_times):.2f} points/s")
            
            # Enregistrement des résultats
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_dir = os.path.join(os.path.dirname(__file__), "results")
            os.makedirs(results_dir, exist_ok=True)
            
            # Sauvegarde CSV
            csv_path = os.path.join(results_dir, f"sweep_benchmark_m{m_value}_{timestamp}.csv")
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["freq_time", "acq_time", "total_time"])
                writer.writeheader()
                writer.writerows(sequences)
            
            # Tracé des graphiques
            plt.figure(figsize=(15, 10))
            
            # 1. Distribution des temps
            plt.subplot(2, 2, 1)
            plt.hist(total_times, bins=50)
            plt.title(f'Distribution du temps total (m={m_value})')
            plt.xlabel('Temps (ms)')
            plt.ylabel('Fréquence')
            plt.grid(True)
            
            # 2. Évolution des temps
            plt.subplot(2, 2, 2)
            plt.plot(range(len(sequences)), total_times, label='Total')
            plt.plot(range(len(sequences)), freq_times, label='Fréquence')
            plt.plot(range(len(sequences)), acq_times, label='Acquisition')
            plt.title(f'Évolution des temps (m={m_value})')
            plt.xlabel('Numéro de séquence')
            plt.ylabel('Temps (ms)')
            plt.legend()
            plt.grid(True)
            
            # 3. Comparaison des composantes
            plt.subplot(2, 2, 3)
            plt.boxplot([freq_times, acq_times, total_times], 
                       labels=['Changement\nfreq', 'Acquisition', 'Total'])
            plt.title(f'Comparaison des temps (m={m_value})')
            plt.ylabel('Temps (ms)')
            plt.grid(True)
            
            # 4. Débit
            plt.subplot(2, 2, 4)
            sweep_rate = 1000 / statistics.mean(total_times)
            plt.bar(['Débit'], [sweep_rate])
            plt.title(f'Débit du sweep (m={m_value})')
            plt.ylabel('Points/s')
            plt.grid(True)
            
            plt.tight_layout()
            fig_path = os.path.join(results_dir, f"sweep_benchmark_m{m_value}_{timestamp}.png")
            plt.savefig(fig_path)
            plt.close()
            
            print(f"\nRésultats enregistrés dans {csv_path}")
            print(f"Graphiques enregistrés dans {fig_path}")
            
            return sequences
        else:
            print("Aucune mesure valide obtenue")
            return None

if __name__ == "__main__":
    # Configuration
    PORT = "COM10"  # À adapter selon votre configuration
    BAUD = 1500000
    QUICK_TEST = True  # Mode test rapide activé par défaut

    benchmark = CommunicationBenchmark(PORT, BAUD, QUICK_TEST)

    print("Choisissez le type de benchmark :")
    print("1. Benchmark lecture synchrone (acquisition mXX*)")
    print("2. Benchmark écriture/configuration (aXX*/dYY*)")
    print("3. Sweep débit en fonction du facteur de moyennage (lecture mXX*)")
    print("4. Test spécifique autour de la valeur 128")
    print("5. Benchmark sweep fréquentiel (changement freq + acquisition)")
    choix = input("Votre choix (1/2/3/4/5) : ").strip()

    if choix == "1":
        m_value = input("Facteur de moyennage (ex: 32) : ").strip()
        try:
            m_value = int(m_value)
        except Exception:
            m_value = 32
        duration = input("Durée du test en secondes (ex: 10) : ").strip()
        try:
            duration = float(duration)
        except Exception:
            duration = 10.0
        benchmark.run_acquisition_benchmark_sync(m_value=m_value, duration=duration)
    elif choix == "2":
        if benchmark.connect():
            try:
                benchmark.run_all_benchmarks()
            finally:
                benchmark.disconnect()
        else:
            print("Impossible de se connecter au port série")
    elif choix == "3":
        mode = input("Mode test (1: rapide, 2: complet) [1] : ").strip()
        quick_test = mode != "2"
        
        duration = input("Durée du test par point (en secondes, ex: 5) : ").strip()
        try:
            duration = float(duration)
        except Exception:
            duration = 5.0
            
        benchmark.sweep_acquisition_benchmark_sync(duration=duration, quick_test=quick_test)
    elif choix == "4":
        duration = input("Durée du test par point (en secondes, ex: 5) : ").strip()
        try:
            duration = float(duration)
        except Exception:
            duration = 5.0
        benchmark.test_around_128(duration=duration)
    elif choix == "5":
        m_value = input("Facteur de moyennage (ex: 32) : ").strip()
        try:
            m_value = int(m_value)
        except Exception:
            m_value = 32
        duration = input("Durée du test en secondes (ex: 10) : ").strip()
        try:
            duration = float(duration)
        except Exception:
            duration = 10.0
        benchmark.benchmark_freq_sweep_sequence(duration=duration, m_value=m_value)
    else:
        print("Choix non reconnu. Arrêt.") 