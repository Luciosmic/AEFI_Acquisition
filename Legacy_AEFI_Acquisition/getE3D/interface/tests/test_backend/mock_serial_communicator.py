"""
Mock SerialCommunicator pour tests d'intégration backend
Conforme à la todo Backend_Testing_Strategy_tasks.md (niveau 3)
"""
import random
import threading
import time

class MockSerial:
    """Objet factice pour simuler un port série"""
    def __init__(self):
        self.is_open = True
    def close(self):
        self.is_open = False

class MockSerialCommunicator:
    """
    Mock complet pour simuler l'interface SerialCommunicator
    - Méthodes : fast_acquisition_m127()
    - Attributs : memory_state, ser
    - Simulation réaliste : valeurs, timing, erreurs
    """
    def __init__(self, connected=True, error_mode=None, gain=1, freq_hz=500, latency_ms=5):
        self.connected = connected
        self.error_mode = error_mode  # None, 'timeout', 'exception'
        self.gain = gain
        self.freq_hz = freq_hz
        self.latency_ms = latency_ms
        self.memory_state = {
            'gain_adc1': gain,
            'gain_adc2': gain,
            'freq_hz': freq_hz,
            'n_avg': 10
        }
        self.ser = MockSerial()
        self._lock = threading.Lock()

    def fast_acquisition_m127(self):
        """
        Simule la lecture d'une ligne d'acquisition :
        "val1\tval2\t...\tval8\t"
        - Valeurs dans le range ADC 24 bits [-8388608, 8388607]
        - Simule latence et erreurs
        """
        if not self.connected:
            raise RuntimeError("Port série déconnecté")
        if self.error_mode == 'timeout':
            time.sleep(1.0)  # Simule un gros timeout
            raise TimeoutError("Timeout simulé")
        if self.error_mode == 'exception':
            raise IOError("Erreur simulée")
        time.sleep(self.latency_ms / 1000.0)
        # Génère 8 valeurs ADC réalistes
        adc_min, adc_max = -8388608, 8388607
        values = [str(random.randint(adc_min, adc_max)) for _ in range(8)]
        return "\t".join(values) + "\t"

    def set_connected(self, state: bool):
        self.connected = state
    def set_error_mode(self, mode: str):
        self.error_mode = mode
    def set_gain(self, gain: int):
        self.gain = gain
        self.memory_state['gain_adc1'] = gain
        self.memory_state['gain_adc2'] = gain
    def set_freq(self, freq_hz: float):
        self.freq_hz = freq_hz
        self.memory_state['freq_hz'] = freq_hz
    def set_latency(self, latency_ms: int):
        self.latency_ms = latency_ms 