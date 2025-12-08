#!/usr/bin/env python3
"""
Module de communication avec la carte constitué d'un AD9106 (DDS) et de deux ADS131A04 (ADC)
Sépare la logique de communication de l'interface graphique

Note: 
- Les paramètres et adresses matérielles sont documentés dans le fichier
ADC_DDS_Configuration_Parameters.json. Ce fichier contient la documentation
technique complète et à jour des adresses et paramètres du matériel.

IMPORTANT:
- Les réglages de l'offset AC et de la valeur en mode DC ne sont forcément valides
- Les réglages de fréquence, de phase, de gain ainsi que de mode (AC/DC) sont bien configurés

"""

import serial
import time
import json
import os
from threading import Thread, Lock
from queue import Queue, Empty
import logging

class SerialCommunicator:
    """Classe gérant la communication série avec la carte DDS/ADC"""
    
    DDS_ADDRESSES = {
        "Frequency": [62, 63],   # 62: MSB, 63: LSB
        "Mode": 39,              # Mode combiné pour DDS1 et DDS2
        "Mode_3_4": 38,          # Mode pour DDS3 et DDS4 (adresse 38)
        "Gain": {1: 53, 2: 52, 3: 51, 4: 50},  # Gain DDS1-4
        "Offset": {1: 37, 2: 36, 3: 38, 4: 38},  # Offset DDS1-4
        "Phase": {1: 67, 2: 66, 3: 65, 4: 64},    # Phase DDS1-4
        "Const": {1: 49, 2: 48, 3: 47, 4: 46}     # Constante DDS1-4
    }

    DDS_MODES = {
        1: {"AC": 49, "DC": 1},          # DDS1: AC = 49, DC = 1
        2: {"AC": 12544, "DC": 256},     # DDS2: AC = 12544, DC = 256
        3: {"AC": 49, "DC": 1},          # DDS3: AC = 49, DC = 1
        4: {"AC": 12544, "DC": 256}      # DDS4: AC = 12544, DC = 256
    }

    def __init__(self, port=None, baudrate=1500000):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.lock = Lock()
        self.logger = logging.getLogger(__name__)
        self.memory_state = {
            "DDS": {
                "Frequence": 1000,
                "Mode": {1: "AC", 2: "AC", 3: "AC", 4: "AC"},
                "Gain": {1: 5000, 2: 5000, 3: 10000, 4: 10000},
                "Offset": {1: 0, 2: 0, 3: 0, 4: 0},
                "Phase": {1: 0, 2: 32768, 3: 16384, 4: 0},
                "Const": {1: 0, 2: 0, 3: 0, 4: 0}
            },
            "ADC": {
                "CLKIN_divider_ratio": 2,
                "ICLK_divider_ratio": 2,
                "Oversampling_ratio": 32,
                "Gain": {1: 0, 2: 0, 3: 0, 4: 0}
            }
        }

    
    def init_default_config(self):
        """
        Initialise le système avec la configuration par défaut (banc typique).
        - Modes DDS en AC+AC
        - Offsets numériques DAC à 0
        - Gains DDS à 10000
        - Autres paramètres selon le tableau de référence
        """
        params_default = [
            (13, 2),      # ADC: CLKIN_divider_ratio
            (14, 32),     # ADC: ICLK_divider_ratio + Oversampling_ratio
            (17, 0),      # ADC: Gain_ADC_1
            (18, 0),      # ADC: Gain_ADC_2
            (19, 0),      # ADC: Gain_ADC_3
            (20, 0),      # ADC: Gain_ADC_4
            (63, 12583),  # DDS: Frequence_DDS (LSB)
            (62, 8),      # DDS: Frequence_DDS (MSB)
            (38, 12593),  # DDS: Mode DDS3+DDS4 (AC+AC)
            (39, 12593),  # DDS: Mode DDS1+DDS2 (AC+AC)
            (34, 0),      # DAC4DOF (Offset numérique DAC4)
            (35, 0),      # DAC3DOF (Offset numérique DAC3)
            (36, 0),      # DAC2DOF (Offset numérique DAC2)
            (37, 0),      # DAC1DOF (Offset numérique DAC1)
            (49, 0),      # DDS: Const_1
            (53, 10000),  # DDS: Gain_1
            (67, 0),      # DDS: Phase_1
            (48, 0),      # DDS: Const_2
            (52, 10000),  # DDS: Gain_2
            (66, 0),      # DDS: Phase_2
            (47, 0),      # DDS: Const_3
            (51, 10000),  # DDS: Gain_3
            (65, 16384),  # DDS: Phase_3
            (46, 0),      # DDS: Const_4
            (50, 10000),  # DDS: Gain_4
            (64, 0),      # DDS: Phase_4
        ]
        for adresse, valeur in params_default:
            self.send_command(f"a{adresse}")
            self.send_command(f"d{valeur}")
        return True, "Initialisation par défaut terminée"


# FONCTIONS UTILITAIRES

    def connect(self, port=None, baudrate=None):
        """Établit la connexion série avec la carte"""
        if port:
            self.port = port
        if baudrate:
            self.baudrate = baudrate
            
        if not self.port:
            return False, "Port série non spécifié"
            
        try:
            # Fermer la connexion existante si ouverte
            if self.ser and self.ser.is_open:
                self.ser.close()
                
            # Ouvrir une nouvelle connexion avec optimisations
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=8,
                stopbits=serial.STOPBITS_ONE,
                parity=serial.PARITY_NONE,
                timeout=1,
                write_timeout=1,      # Évite les blocages à l'écriture
                inter_byte_timeout=None,  # Pas de timeout inter-caractères
                exclusive=True        # Accès exclusif (si supporté)
            )
            
            return True, "Connexion établie"
        except Exception as e:
            return False, f"Erreur de connexion: {str(e)}"
    
    def disconnect(self):
        """Ferme la connexion série"""
        if self.ser and self.ser.is_open:
            self.ser.close()
    
    def clear_serial_buffer(self):
        """Vide le buffer d'entrée série"""
        if self.ser and self.ser.is_open:
            self.ser.reset_input_buffer()
    
    def send_command(self, command):
        """Version optimisée avec protocole correct à deux lectures pour acquisitions"""
        if not self.ser or not self.ser.is_open:
            return False, "Port série non connecté"
        
        with self.lock:
            try:
                # S'assurer que la commande se termine par '*'
                if not command.endswith('*'):
                    command += '*'
                    
                # Envoyer la commande
                self.ser.write(command.encode())
                
                # Pour les commandes d'acquisition (m), protocole à deux lectures
                if command.startswith('m') and command[1:].replace('*', '').isdigit():
                    # Première lecture : confirmation (ex: "m=  127\n")
                    confirmation = self.ser.readline()
                    # Seconde lecture : les vraies données (ex: "3789\t3181\t3071\t3113\t1666\t1987\t2351\t2212\t\n")
                    data_response = self.ser.readline()
                    return True, data_response.decode('ascii', errors='ignore').rstrip('\r\n')
                else:
                    # Pour les autres commandes, une seule lecture
                    response = self.ser.readline()
                    return True, response.decode('ascii', errors='ignore').rstrip('\r\n')
                
            except Exception as e:
                return False, f"Erreur de communication: {str(e)}"
    
    def get_memory_state(self):
        """Retourne une copie de l'état mémoire logiciel du banc."""
        import copy
        return copy.deepcopy(self.memory_state)

# FONCTIONS D'ACQUISITION


    
    def acquisition(self, n_avg=127):
        """
        Acquisition avec moyennage configurable
        Args:
            n_avg: Nombre de moyennage (1, 32, 64, 127, etc.)
        """
        if not self.ser or not self.ser.is_open:
            return False, ""
        
        with self.lock:
            try:
                command = f'm{n_avg}*'.encode()
                self.ser.write(command)
                
                # Lire la confirmation
                confirmation = self.ser.readline()
                
                # Lire les données d'acquisition
                data_response = self.ser.readline()
                data_str = data_response.decode('ascii', errors='ignore').rstrip('\r\n')
                return True, data_str
                
            except Exception as e:
                return False, f"Erreur acquisition: {str(e)}"


# REGLAGE DDS
    def _freq_to_uint32(self, freq):
        """Convertit une fréquence en valeur 32 bits non signée"""
        resultat = freq * (2**32) / 16_000_000
        resultat_entier = int(round(resultat))
        
        if not (0 <= resultat_entier <= 4294967295):
            return False, f"Résultat {resultat_entier} hors de la plage uint32"
        
        return True, resultat_entier
    
    def _decomposer_uint32(self, valeur_32bits):
        """Décompose un entier 32 bits en partie haute (16 bits MSB) et partie basse (16 bits LSB)"""
        if not (0 <= valeur_32bits <= 4294967295):
            return False, f"Valeur {valeur_32bits} hors de la plage uint32"
        
        partie_haute = (valeur_32bits >> 16) & 0xFFFF
        partie_basse = valeur_32bits & 0xFFFF
        
        return True, (partie_haute, partie_basse)

    def set_dds_frequency(self, freq):
        """Configure la fréquence des DDS"""
        success, result = self._freq_to_uint32(freq)
        if not success:
            return False, result
        valeur_32bits = result
        success, result = self._decomposer_uint32(valeur_32bits)
        if not success:
            return False, result
        partie_haute, partie_basse = result
        success, response = self.send_command(f"a{self.DDS_ADDRESSES['Frequency'][0]}")
        if not success:
            return False, f"Erreur lors de l'envoi de l'adresse MSB: {response}"
        success, response = self.send_command(f"d{partie_haute}")
        if not success:
            return False, f"Erreur lors de l'envoi de la valeur MSB: {response}"
        success, response = self.send_command(f"a{self.DDS_ADDRESSES['Frequency'][1]}")
        if not success:
            return False, f"Erreur lors de l'envoi de l'adresse LSB: {response}"
        success, response = self.send_command(f"d{partie_basse}")
        if not success:
            return False, f"Erreur lors de l'envoi de la valeur LSB: {response}"
        # MAJ mémoire
        self.memory_state["DDS"]["Frequence"] = freq
        return True, f"Fréquence configurée à {freq} Hz"
           
    def set_dds_modes(self, dds1_ac: bool, dds2_ac: bool, dds3_ac: bool, dds4_ac: bool):
        """
        Configure les modes (AC/DC) pour les quatre DDS en tenant compte des registres partagés.

        Args:
            dds1_ac (bool): True pour AC, False pour DC sur DDS1.
            dds2_ac (bool): True pour AC, False pour DC sur DDS2.
            dds3_ac (bool): True pour AC, False pour DC sur DDS3.
            dds4_ac (bool): True pour AC, False pour DC sur DDS4.
        """
        try:
            mode1_val = self.DDS_MODES[1]["AC"] if dds1_ac else self.DDS_MODES[1]["DC"]
            mode2_val = self.DDS_MODES[2]["AC"] if dds2_ac else self.DDS_MODES[2]["DC"]
            valeur_dds12 = mode1_val + mode2_val
            self.send_command(f"a{self.DDS_ADDRESSES['Mode']}")
            self.send_command(f"d{valeur_dds12}")
            self.memory_state["DDS"]["Mode"] = {
                1: "AC" if dds1_ac else "DC",
                2: "AC" if dds2_ac else "DC",
                3: "AC" if dds3_ac else "DC",
                4: "AC" if dds4_ac else "DC"
            }
            return True, "Modes DDS configurés avec succès."
        except KeyError as e:
            msg = f"Erreur de configuration: clé de mode DDS manquante: {e}"
            self.logger.error(msg)
            return False, msg
        except Exception as e:
            msg = f"Erreur inattendue lors de la configuration des modes DDS: {e}"
            self.logger.error(msg)
            return False, msg

    def set_dds_gain(self, channel, value):
        """Configure le gain d'un canal DDS"""
        if not (1 <= channel <= 4) or not (0 <= value <= 16376):
            return False, "Paramètres invalides"
        
        # Adresse selon le canal
        addr = self.DDS_ADDRESSES["Gain"][channel]
        
        success, response = self.send_command(f"a{addr}")
        if not success:
            return False, f"Erreur lors de l'envoi de l'adresse de gain: {response}"
        
        success, response = self.send_command(f"d{value}")
        if not success:
            return False, f"Erreur lors de l'envoi de la valeur de gain: {response}"
        
        # MAJ mémoire
        self.memory_state["DDS"]["Gain"][channel] = value
        
        return True, f"Gain DDS{channel} configuré à {value}"
    
    def set_dds_offset(self, channel, value):
        """Configure l'offset d'un canal DDS"""
        if not (1 <= channel <= 4) or not (0 <= value <= 65535):
            return False, "Paramètres invalides"
        
        # Adresse selon le canal
        addr = self.DDS_ADDRESSES["Offset"][channel]
        
        success, response = self.send_command(f"a{addr}")
        if not success:
            return False, f"Erreur lors de l'envoi de l'adresse d'offset: {response}"
        
        success, response = self.send_command(f"d{value}")
        if not success:
            return False, f"Erreur lors de l'envoi de la valeur d'offset: {response}"
        
        # MAJ mémoire
        self.memory_state["DDS"]["Offset"][channel] = value
        
        return True, f"Offset DDS{channel} configuré à {value}"
    
    def set_dds_phase(self, channel, value):
        """Configure la phase d'un canal DDS"""
        if not (1 <= channel <= 4) or not (0 <= value <= 65535):
            return False, "Paramètres invalides"
        
        # Adresse selon le canal
        addr = self.DDS_ADDRESSES["Phase"][channel]
        
        success, response = self.send_command(f"a{addr}")
        if not success:
            return False, f"Erreur lors de l'envoi de l'adresse de phase: {response}"
        
        success, response = self.send_command(f"d{value}")
        if not success:
            return False, f"Erreur lors de l'envoi de la valeur de phase: {response}"
        
        # MAJ mémoire
        self.memory_state["DDS"]["Phase"][channel] = value
        
        return True, f"Phase DDS{channel} configurée à {value}"
    
    def set_dds_const(self, channel, value):
        """Configure la constante DC d'un canal DDS"""
        if not (1 <= channel <= 4) or not (0 <= value <= 65535):
            return False, "Paramètres invalides"
        
        # Adresse selon le canal
        addr = self.DDS_ADDRESSES["Const"][channel]
        
        success, response = self.send_command(f"a{addr}")
        if not success:
            return False, f"Erreur lors de l'envoi de l'adresse de constante: {response}"
        
        success, response = self.send_command(f"d{value}")
        if not success:
            return False, f"Erreur lors de l'envoi de la valeur de constante: {response}"
        
        # MAJ mémoire
        self.memory_state["DDS"]["Const"][channel] = value
        
        return True, f"Constante DC DDS{channel} configurée à {value}"
    
    def set_dds1_mode(self, mode):
        """Change uniquement le mode de DDS1 (AC/DC) sans toucher DDS2."""
        val1 = self.DDS_MODES[1][mode]
        mode2 = self.memory_state["DDS"]["Mode"][2]
        val2 = self.DDS_MODES[2][mode2]
        valeur = val1 + val2
        self.send_command(f"a{self.DDS_ADDRESSES['Mode']}")
        self.send_command(f"d{valeur}")
        self.memory_state["DDS"]["Mode"][1] = mode

    def set_dds2_mode(self, mode):
        """Change uniquement le mode de DDS2 (AC/DC) sans toucher DDS1."""
        val2 = self.DDS_MODES[2][mode]
        mode1 = self.memory_state["DDS"]["Mode"][1]
        val1 = self.DDS_MODES[1][mode1]
        valeur = val1 + val2
        self.send_command(f"a{self.DDS_ADDRESSES['Mode']}")
        self.send_command(f"d{valeur}")
        self.memory_state["DDS"]["Mode"][2] = mode

    def set_dds3_mode(self, mode):
        """Change uniquement le mode de DDS3 (AC/DC) sans toucher DDS4."""
        val3 = self.DDS_MODES[3][mode]
        mode4 = self.memory_state["DDS"]["Mode"][4]
        val4 = self.DDS_MODES[4][mode4]
        valeur = val3 + val4
        self.send_command(f"a{self.DDS_ADDRESSES['Mode_3_4']}")
        self.send_command(f"d{valeur}")
        self.memory_state["DDS"]["Mode"][3] = mode

    def set_dds4_mode(self, mode):
        """Change uniquement le mode de DDS4 (AC/DC) sans toucher DDS3."""
        val4 = self.DDS_MODES[4][mode]
        mode3 = self.memory_state["DDS"]["Mode"][3]
        val3 = self.DDS_MODES[3][mode3]
        valeur = val3 + val4
        self.send_command(f"a{self.DDS_ADDRESSES['Mode_3_4']}")
        self.send_command(f"d{valeur}")
        self.memory_state["DDS"]["Mode"][4] = mode



# REGLAGE ADC
    def set_adc_gain(self, channel, value):
        """Configure le gain d'un canal ADC"""
        if not (1 <= channel <= 4) or value not in [1, 2, 4, 8, 16]:
            return False, "Paramètres invalides"
        
        # Adresse selon le canal et correspondance des valeurs
        addresses = {1: 17, 2: 18, 3: 19, 4: 20}
        gains_values = {1: 0, 2: 1, 4: 2, 8: 3, 16: 4}  # Conversion gain -> valeur à envoyer
        
        addr = addresses.get(channel)
        value_to_send = gains_values.get(value, 0)  # Valeur par défaut: 0 (gain de 1)
        
        success, response = self.send_command(f"a{addr}")
        if not success:
            return False, f"Erreur lors de l'envoi de l'adresse de gain ADC: {response}"
        
        success, response = self.send_command(f"d{value_to_send}")
        if not success:
            return False, f"Erreur lors de l'envoi de la valeur de gain ADC: {response}"
        
        # MAJ mémoire
        self.memory_state["ADC"]["Gain"][channel] = value
        
        return True, f"Gain du ADC {channel} configuré à {value}"
    
    def _clkin_value_to_code(self, value):
        """Convertit la valeur CLKIN divider ratio en code à envoyer (0-7)"""
        value_map = {
            0: 0,  # Reserved
            2: 1,
            4: 2,
            6: 3,
            8: 4,
            10: 5,
            12: 6,
            14: 7
        }
        return value_map.get(value, 1)  # Défaut: 1 (pour 2)
    
    def _iclk_value_to_code(self, value):
        """Convertit la valeur ICLK divider ratio en code à envoyer (0-7)"""
        value_map = {
            0: 0,  # Reserved
            2: 1,
            4: 2,
            6: 3,
            8: 4,
            10: 5,
            12: 6,
            14: 7
        }
        return value_map.get(value, 1)  # Défaut: 1 (pour 2)
    
    def _oversampling_value_to_code(self, value):
        """Convertit la valeur d'oversampling en code à envoyer (0-15)"""
        value_map = {
            4096: 0,
            2048: 1,
            1024: 2,
            800: 3,
            768: 4,
            512: 5,
            400: 6,
            384: 7,
            256: 8,
            200: 9,
            192: 10,
            128: 11,
            96: 12,
            64: 13,
            48: 14,
            32: 15
        }
        return value_map.get(value, 0)  # Défaut: 0 (pour 4096)
    
    def set_clkin_divider(self, value):
        """Configure le CLKIN divider ratio"""
        if value not in [0, 2, 4, 6, 8, 10, 12, 14]:
            return False, "Valeur invalide"
        
        # Conversion en code
        code_value = self._clkin_value_to_code(value)
        
        self.send_command(f"a13")
        self.send_command(f"d{code_value}")
        
        # MAJ mémoire
        self.memory_state["ADC"]["CLKIN_divider_ratio"] = value
        
        return True, f"CLKIN divider ratio configuré à {value} (code: {code_value})"
    
    def set_iclk_divider_and_oversampling(self, iclk_value, oversampling_value):
        """Configure conjointement ICLK divider ratio et Oversampling ratio"""
        if iclk_value not in [0, 2, 4, 6, 8, 10, 12, 14]:
            return False, "Valeur ICLK invalide"
            
        valid_oversampling_values = [4096, 2048, 1024, 800, 768, 512, 400, 384, 256, 200, 192, 128, 96, 64, 48, 32]
        if oversampling_value not in valid_oversampling_values:
            return False, "Valeur Oversampling invalide"
        
        # Conversion en codes
        iclk_code = self._iclk_value_to_code(iclk_value)
        oversampling_code = self._oversampling_value_to_code(oversampling_value)
        
        # Calcul de la valeur combinée : iclk_code * 36 + oversampling_code
        combined_value = (iclk_code * 36) + oversampling_code
        
        self.send_command(f"a14")
        self.send_command(f"d{combined_value}")
        
        # MAJ mémoire
        self.memory_state["ADC"]["ICLK_divider_ratio"] = iclk_value
        self.memory_state["ADC"]["Oversampling_ratio"] = oversampling_value
        
        return True, f"ICLK divider ({iclk_value}) et Oversampling ratio ({oversampling_value}) configurés (code: {combined_value})"
    
    def set_iclk_divider(self, value):
        """Configure uniquement ICLK divider ratio en préservant l'Oversampling ratio existant"""
        if value not in [0, 2, 4, 6, 8, 10, 12, 14]:
            return False, "Valeur invalide"
        
        # Récupérer la valeur actuelle d'oversampling
        current_oversampling = 4096  # Valeur par défaut
        if "ADC" in self.memory_state and "Oversampling_ratio" in self.memory_state["ADC"]:
            current_oversampling = self.memory_state["ADC"]["Oversampling_ratio"]
        
        # Appeler la méthode commune
        return self.set_iclk_divider_and_oversampling(value, current_oversampling)
    
    def set_oversampling_ratio(self, value):
        """Configure uniquement Oversampling ratio en préservant l'ICLK divider ratio existant"""
        valid_values = [4096, 2048, 1024, 800, 768, 512, 400, 384, 256, 200, 192, 128, 96, 64, 48, 32]
        if value not in valid_values:
            return False, "Valeur invalide"
        
        # Récupérer la valeur actuelle de ICLK
        current_iclk = 2  # Valeur par défaut
        if "ADC" in self.memory_state and "ICLK_divider_ratio" in self.memory_state["ADC"]:
            current_iclk = self.memory_state["ADC"]["ICLK_divider_ratio"]
        
        # Appeler la méthode commune
        return self.set_iclk_divider_and_oversampling(current_iclk, value)
    
    def set_reference_config(self, negative_ref=False, high_res=True, ref_voltage=1, ref_selection=1):
        """Configure les références ADC (adresse 11)"""
        val_combinee = 0
        
        # Negative reference (bit 7)
        if negative_ref:
            val_combinee += 128
            
        # High resolution (bit 6)
        if high_res:
            val_combinee += 64
            
        # Reference voltage (0=2.442V, 1=4.0V)
        if ref_voltage == 1:
            val_combinee += 16
            
        # Reference selection (0=External, 1=Internal)
        if ref_selection == 1:
            val_combinee += 8
        
        success, response = self.send_command(f"a11")
        if not success:
            return False, f"Erreur lors de l'envoi de l'adresse de référence: {response}"
        
        success, response = self.send_command(f"d{val_combinee}")
        if not success:
            return False, f"Erreur lors de l'envoi de la valeur de référence: {response}"
        
        # MAJ mémoire
        self.memory_state["ADC"]["References_Configuration"] = {
            "options": {
                "Negative_Reference": {"valeur": negative_ref},
                "High_Resolution": {"valeur": high_res},
                "Reference_Voltage": {"valeur": ref_voltage},
                "Reference_Selection": {"valeur": ref_selection}
            },
            "valeur": val_combinee
        }
        
        return True, f"Références configurées (valeur: {val_combinee})"
    
# Test du module si exécuté directement
if __name__ == "__main__":
    communicator = SerialCommunicator()
    
    # Exemple d'utilisation
    port = "COM10"  # À adapter
    success, message = communicator.connect(port)
    if success:
        print(f"Connecté à {port}")
        
        # Exemple : configurer la fréquence
        success, message = communicator.set_dds_frequency(1000)
        print(f"Fréquence: {message}")
        
        # Exemple : configurer les modes
        success, message = communicator.set_dds_modes(True, False, True, False)
        print(f"Modes: {message}")
        
        # Fermer la connexion
        communicator.disconnect()
        print("Connexion fermée")
    else:
        print(f"Erreur de connexion: {message}")
