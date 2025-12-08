import os
import time
import csv
from datetime import datetime
import sys

# Import du communicateur LSM9D
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'instrument')))
from LSM9D_SerialCommunication import LSM9D_SerialCommunicator

# Paramètres du benchmark
BENCHMARK_DURATION = 60  # secondes pour le débit
LATENCY_TESTS = 100       # nombre de mesures de latence
EXPORT_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(EXPORT_DIR, exist_ok=True)


def benchmark_streaming(communicator, duration=BENCHMARK_DURATION):
    """Mesure le débit d'acquisition en mode streaming sur 'duration' secondes."""
    print("--- Benchmark Débit (streaming ALL_SENSORS) ---")
    data_points = []
    start_time = time.time()
    end_time = start_time + duration

    def on_data():
        data_points.append(time.time())

    communicator.add_data_callback(on_data)
    communicator.connect()
    communicator.initialize_sensor_mode('ALL_SENSORS')
    communicator.start_streaming()
    print(f"Streaming démarré pour {duration}s...")
    while time.time() < end_time:
        time.sleep(0.05)
    communicator.stop_streaming()
    communicator.disconnect()

    n = len(data_points)
    if n < 2:
        print("Pas assez de données pour calculer le débit.")
        return 0, []
    elapsed = data_points[-1] - data_points[0]
    rate = (n - 1) / elapsed if elapsed > 0 else 0
    print(f"Nombre d'échantillons : {n}")
    print(f"Durée effective : {elapsed:.2f} s")
    print(f"Débit moyen : {rate:.2f} Hz")
    return rate, data_points


def benchmark_latency(communicator, n_tests=LATENCY_TESTS):
    """Mesure la latence aller-retour d'une commande de lecture (hors streaming)."""
    print("\n--- Benchmark Latence (commande/réponse ALL_SENSORS) ---")
    latencies = []
    communicator.connect()
    communicator.initialize_sensor_mode('ALL_SENSORS')
    time.sleep(0.5)
    for i in range(n_tests):
        t0 = time.perf_counter()
        communicator.send_command('S')  # Commande simple (status ou lecture)
        communicator.read_response()
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000)  # ms
        time.sleep(0.1)
    communicator.disconnect()
    print(f"Latence min : {min(latencies):.2f} ms")
    print(f"Latence max : {max(latencies):.2f} ms")
    print(f"Latence moyenne : {sum(latencies)/len(latencies):.2f} ms")
    return latencies


def export_results(rate, data_points, latencies):
    now = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    filename = f"{now}_LSM9D_benchmark_ALLSENSORS.csv"
    filepath = os.path.join(EXPORT_DIR, filename)
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Type", "Valeur"])
        writer.writerow(["Débit (Hz)", f"{rate:.2f}"])
        writer.writerow([])
        writer.writerow(["Latence (ms)"])
        writer.writerow(["min", f"{min(latencies):.2f}"])
        writer.writerow(["max", f"{max(latencies):.2f}"])
        writer.writerow(["moyenne", f"{sum(latencies)/len(latencies):.2f}"])
        writer.writerow([])
        writer.writerow(["Timestamp acquisition (s depuis epoch)"])
        for t in data_points:
            writer.writerow([t])
        writer.writerow([])
        writer.writerow(["Latences individuelles (ms)"])
        for l in latencies:
            writer.writerow([l])
    print(f"\nRésultats exportés dans : {filepath}")


def main():
    communicator = LSM9D_SerialCommunicator()
    rate, data_points = benchmark_streaming(communicator)
    latencies = benchmark_latency(communicator)
    export_results(rate, data_points, latencies)

if __name__ == "__main__":
    main()
