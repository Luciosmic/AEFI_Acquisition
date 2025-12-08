# cython: language_level=3
"""
Module Cython ultra-optimisé simplifié pour acquisition série haute performance
Version sans erreurs de compilation
"""

import cython
import serial
import time

cdef class UltraSerialCython:
    """Communicateur série optimisé avec Cython - Version simplifiée"""
    
    cdef:
        object ser
        double last_acquisition_time
        int acquisition_count
        
    def __cinit__(self, port="COM10", int baudrate=1500000):
        """Constructeur Cython simplifié"""
        self.last_acquisition_time = 0.0
        self.acquisition_count = 0
        
        # Initialiser le port série avec configuration optimisée
        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=8,
            stopbits=serial.STOPBITS_ONE,
            parity=serial.PARITY_NONE,
            timeout=0.0635,         # Timeout court car lectures précises
            write_timeout=0.01,
            exclusive=True
        )
        
        # Vider les buffers
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
    
    def __dealloc__(self):
        """Destructeur"""
        if self.ser and self.ser.is_open:
            self.ser.close()
    
    @cython.cdivision(True)
    cdef inline double get_time_ms(self):
        """Obtenir le temps en millisecondes"""
        return time.perf_counter() * 1000.0
    
    def ultra_fast_acquisition_m127(self):
        """Acquisition ultra-optimisée pour m=127 - Version simplifiée"""
        cdef double start_time = self.get_time_ms()
        cdef double end_time
        cdef double duration
        
        try:
            # Test ultra-simple : juste lire ce qui arrive
            self.ser.reset_input_buffer()
            
            # Envoyer commande
            self.ser.write(b'm127*')
            
            # Retour à la méthode stable : 9+99 octets
            confirmation_data = self.ser.read(9)
            real_data = self.ser.read(99)
            
            # Parsing optimisé : extraire seulement les vraies données
            full_data = confirmation_data + real_data
            data_str = full_data.decode('ascii', errors='ignore')
            
            # Extraire seulement la partie après "m=  127\n"
            newline_pos = data_str.find('\n')
            if newline_pos != -1 and newline_pos < len(data_str) - 1:
                data_str = data_str[newline_pos + 1:].rstrip()
            
            end_time = self.get_time_ms()
            duration = end_time - start_time
            
            # Statistiques
            self.acquisition_count += 1
            self.last_acquisition_time = duration
            
            return True, data_str, duration
            
        except Exception as e:
            end_time = self.get_time_ms()
            duration = end_time - start_time
            return False, str(e), duration
    
    def ultra_fast_acquisition_m1(self):
        """Acquisition ultra-optimisée pour m=1 - Version simplifiée"""
        cdef double start_time = self.get_time_ms()
        cdef double end_time
        cdef double duration
        
        try:
            self.ser.reset_input_buffer()
            self.ser.write(b'm1*')
            confirmation_data = self.ser.read(9)
            real_data = self.ser.read(99)
            full_data = confirmation_data + real_data
            data_str = full_data.decode('ascii', errors='ignore')
            newline_pos = data_str.find('\n')
            if newline_pos != -1 and newline_pos < len(data_str) - 1:
                data_str = data_str[newline_pos + 1:].rstrip()
            end_time = self.get_time_ms()
            duration = end_time - start_time
            self.acquisition_count += 1
            self.last_acquisition_time = duration
            return True, data_str, duration
        except Exception as e:
            end_time = self.get_time_ms()
            duration = end_time - start_time
            return False, str(e), duration
    
    def get_stats(self):
        """Obtenir les statistiques"""
        return {
            "total_acquisitions": self.acquisition_count,
            "last_duration_ms": self.last_acquisition_time,
            "estimated_rate_acqs": 1000.0 / self.last_acquisition_time if self.last_acquisition_time > 0 else 0
        }


def test_cython_performance(int n_tests=20):
    """Fonction de test simple pour le module Cython"""
    print("=== TEST PERFORMANCE CYTHON ===")
    
    # Créer l'instance
    comm = UltraSerialCython("COM10", 1500000)
    
    print(f"Test avec {n_tests} acquisitions...")
    
    # Préchauffage
    for i in range(3):
        comm.ultra_fast_acquisition_m127()
        time.sleep(0.01)
    
    # Test principal
    times = []
    success_count = 0
    
    for i in range(n_tests):
        success, data, duration_ms = comm.ultra_fast_acquisition_m127()
        times.append(duration_ms)
        
        if success and data.strip():
            success_count += 1
        
        time.sleep(0.005)
    
    # Calculs
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    rate = success_count / (sum(times) / 1000.0)
    success_rate = (success_count / n_tests) * 100.0
    
    print(f"Temps moyen: {avg_time:.2f} ms")
    print(f"Temps min/max: {min_time:.2f}/{max_time:.2f} ms")
    print(f"Débit: {rate:.1f} acq/s")
    print(f"Succès: {success_rate:.1f}%")
    
    # Comparaison avec baseline Python (138ms)
    baseline_python = 138.0
    improvement = baseline_python / avg_time
    print(f"\nAmélioration vs Python: {improvement:.1f}x plus rapide")
    
    if avg_time < 20.0:
        print("🎯 OBJECTIF ATTEINT: <20ms par acquisition")
    else:
        print(f"❌ Objectif manqué: {avg_time:.1f}ms (objectif <20ms)")
    
    return {
        "avg_time_ms": avg_time,
        "rate_acq_s": rate,
        "improvement_factor": improvement,
        "success_rate": success_rate
    } 