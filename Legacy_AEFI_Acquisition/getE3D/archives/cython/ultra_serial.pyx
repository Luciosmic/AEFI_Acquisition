# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
"""
Module Cython ultra-optimisé pour acquisition série haute performance
Objectif: Passer de 7 acq/s (138ms) à 50+ acq/s (<20ms)
"""

import cython
from libc.stdlib cimport malloc, free
from libc.string cimport memset, strcpy
import serial
import time

cdef class UltraSerialCython:
    """Communicateur série optimisé avec Cython"""
    
    cdef:
        object ser                    # Port série Python (PySerial)
        char* buffer                  # Buffer C pour données
        char* command_buffer          # Buffer pour commandes
        int buffer_size
        double last_acquisition_time
        int acquisition_count
        
    def __cinit__(self, port="COM10", int baudrate=1500000):
        """Constructeur Cython avec allocation mémoire C"""
        self.buffer_size = 1024
        self.buffer = <char*>malloc(self.buffer_size * sizeof(char))
        self.command_buffer = <char*>malloc(64 * sizeof(char))
        self.last_acquisition_time = 0.0
        self.acquisition_count = 0
        
        if self.buffer is NULL or self.command_buffer is NULL:
            raise MemoryError("Impossible d'allouer les buffers")
            
        # Initialiser le port série
        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=8,
            stopbits=serial.STOPBITS_ONE,
            parity=serial.PARITY_NONE,
            timeout=0.005,        # Timeout ultra-court: 5ms
            write_timeout=0.005,
            exclusive=True
        )
        
        # Optimiser les buffers série si possible
        try:
            self.ser.set_buffer_size(rx_size=256, tx_size=64)
        except:
            pass
    
    def __dealloc__(self):
        """Destructeur pour libérer la mémoire"""
        if self.buffer is not NULL:
            free(self.buffer)
        if self.command_buffer is not NULL:
            free(self.command_buffer)
        if self.ser and self.ser.is_open:
            self.ser.close()
    
    @cython.cdivision(True)
    cdef inline double get_time_ms(self):
        """Obtenir le temps en millisecondes avec précision maximale"""
        return time.perf_counter() * 1000.0
    
    cdef int send_command_fast(self, char* command) nogil:
        """Envoi de commande optimisé (sans GIL)"""
        cdef int command_len = 0
        
        # Calculer la longueur de la commande
        while command[command_len] != 0:
            command_len += 1
            if command_len > 60:  # Sécurité
                break
        
        return command_len
    
    @cython.boundscheck(False)
    @cython.wraparound(False)
    def ultra_fast_acquisition_m127(self):
        """Acquisition ultra-optimisée pour m=127"""
        cdef double start_time = self.get_time_ms()
        cdef bytes data_bytes
        cdef str data_str
        cdef double end_time
        cdef double duration
        
        try:
            # Vider les buffers d'entrée
            self.ser.reset_input_buffer()
            
            # Envoyer la commande directement
            self.ser.write(b'm127*')
            self.ser.flush()
            
            # Lecture optimisée en deux étapes
            # Étape 1: Lire la confirmation
            confirmation = self.ser.readline()
            
            # Étape 2: Lire les données
            data_bytes = self.ser.readline()
            
            # Conversion et nettoyage optimisés
            data_str = data_bytes.decode('ascii', errors='ignore').rstrip('\r\n\t ')
            
            end_time = self.get_time_ms()
            duration = end_time - start_time
            
            # Statistiques internes
            self.acquisition_count += 1
            self.last_acquisition_time = duration
            
            return True, data_str, duration
            
        except Exception as e:
            end_time = self.get_time_ms()
            duration = end_time - start_time
            return False, str(e), duration
    
    @cython.boundscheck(False) 
    def ultra_fast_acquisition_block(self):
        """Version avec lecture en bloc pour performance maximale"""
        cdef double start_time = self.get_time_ms()
        cdef bytes raw_data
        cdef str data_str
        cdef int newline_pos
        cdef double end_time
        cdef double duration
        
        try:
            # Vider buffer
            self.ser.reset_input_buffer()
            
            # Commande
            self.ser.write(b'm127*')
            self.ser.flush()
            
            # Lecture en bloc (estimation: 8 + 56 = 64 caractères)
            raw_data = self.ser.read(80)
            
            # Parsing ultra-rapide
            data_str = raw_data.decode('ascii', errors='ignore')
            
            # Trouver le premier \n (fin de confirmation)
            newline_pos = data_str.find('\n')
            if newline_pos != -1:
                # Extraire la partie données
                data_part = data_str[newline_pos + 1:].rstrip('\r\n\t\x00 ')
                
                end_time = self.get_time_ms()
                duration = end_time - start_time
                
                return True, data_part, duration
            else:
                end_time = self.get_time_ms()
                duration = end_time - start_time
                return False, "Format invalide", duration
                
        except Exception as e:
            end_time = self.get_time_ms()
            duration = end_time - start_time
            return False, str(e), duration
    
    def get_stats(self):
        """Obtenir les statistiques de performance"""
        return {
            "total_acquisitions": self.acquisition_count,
            "last_duration_ms": self.last_acquisition_time,
            "estimated_rate_acqs": 1000.0 / self.last_acquisition_time if self.last_acquisition_time > 0 else 0
        }
    
    def benchmark_methods(self, int n_tests=20):
        """Benchmark des différentes méthodes Cython"""
        cdef list methods = [
            ("readline_optimized", self.ultra_fast_acquisition_m127),
            ("block_reading", self.ultra_fast_acquisition_block)
        ]
        
        results = {}
        
        for method_name, method_func in methods:
            print(f"\n--- Test Cython: {method_name} ---")
            
            # Préchauffage
            for _ in range(3):
                method_func()
                time.sleep(0.01)
            
            # Test principal
            cdef list times = []
            cdef int success_count = 0
            cdef int i
            
            for i in range(n_tests):
                success, data, duration_ms = method_func()
                times.append(duration_ms)
                
                if success and data.strip():
                    success_count += 1
                
                time.sleep(0.002)  # Délai minimal entre acquisitions
            
            # Calculs
            cdef double avg_time = sum(times) / len(times)
            cdef double min_time = min(times)
            cdef double max_time = max(times)
            cdef double rate = success_count / (sum(times) / 1000.0)
            cdef double success_rate = (success_count / <double>n_tests) * 100.0
            
            results[method_name] = {
                "avg_time_ms": round(avg_time, 2),
                "min_time_ms": round(min_time, 2),
                "max_time_ms": round(max_time, 2),
                "rate_acq_s": round(rate, 1),
                "success_rate": round(success_rate, 1)
            }
            
            print(f"  Temps moyen: {avg_time:.2f} ms")
            print(f"  Temps min/max: {min_time:.2f}/{max_time:.2f} ms")
            print(f"  Débit: {rate:.1f} acq/s")
            print(f"  Succès: {success_rate:.1f}%")
        
        return results 