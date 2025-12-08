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
        # print(f"[DEBUG][SerialCommunicator.__init__] Initialisation avec port={port}, baudrate={baudrate}")
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.lock = Lock()
        self.logger = logging.getLogger(__name__)
        self.init_default_config()
        # print(f"[DEBUG][SerialCommunicator.__init__] Fin initialisation, port={self.port}")

    def init_default_config(self):
        """
        Initialise le système avec la configuration par défaut (banc typique).
        - Modes DDS en AC+AC
        - Offsets numériques DAC à 0
        - Gains DDS à 10000
        - Autres paramètres selon le tableau de référence
        """
        # Initialisation cohérente de l'état mémoire 
        # ATTENTION CE DICTIONNAIRE EST ECRASE PAR PARAMS_DEFAULT A L'INITIALISATION
        self.memory_state = {
            "DDS": {
                "Frequence": 1000,
                "Mode": {1: "AC", 2: "AC", 3: "AC", 4: "AC"},
                "Gain": {1: 0000, 2: 0000, 3: 10000, 4: 10000},
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
            (53, 0),  # DDS: Gain_1 --> Pas d'excitation au démarrage sur les poupettes
            (67, 0),      # DDS: Phase_1
            (48, 0),      # DDS: Const_2
            (52, 0),  # DDS: Gain_2 --> Pas d'excitation au démarrage sur les poupettes
            (66, 32768),      # DDS: Phase_2
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
            # Synchronisation automatique de memory_state avec les valeurs réellement envoyées
            self._update_memory_from_address(adresse, valeur)
        return True, "Initialisation par défaut terminée"
    
    def _update_memory_from_address(self, address: int, value: int):
        """Met à jour memory_state en fonction de l'adresse et la valeur"""
        # Mapping adresse → memory_state selon le manuel AD9106/ADS131A04
        
        # === ADC Parameters ===
        if address == 13:    # CLKIN_divider_ratio
            self.memory_state["ADC"]["CLKIN_divider_ratio"] = value
        elif address == 14:  # ICLK_divider_ratio + Oversampling_ratio (combiné)
            # Décoder la valeur combinée (voir manuel ADS131A04)
            self.memory_state["ADC"]["ICLK_divider_ratio"] = value & 0xFF  # 8 bits bas
            self.memory_state["ADC"]["Oversampling_ratio"] = (value >> 8) & 0xFF  # 8 bits hauts
        elif address == 17:  # Gain_ADC_1
            self.memory_state["ADC"]["Gain"][1] = value
        elif address == 18:  # Gain_ADC_2
            self.memory_state["ADC"]["Gain"][2] = value
        elif address == 19:  # Gain_ADC_3
            self.memory_state["ADC"]["Gain"][3] = value
        elif address == 20:  # Gain_ADC_4
            self.memory_state["ADC"]["Gain"][4] = value
            
        # === DDS Frequency (combinée LSB+MSB) ===
        elif address == 63:  # Frequence_DDS (LSB)
            # Stockage temporaire LSB
            if not hasattr(self, '_freq_lsb'):
                self._freq_lsb = 0
            self._freq_lsb = value
            # Calcul fréquence si MSB déjà reçu
            if hasattr(self, '_freq_msb'):
                freq_uint32 = (self._freq_msb << 16) | self._freq_lsb
                freq_hz = self._uint32_to_freq(freq_uint32)
                self.memory_state["DDS"]["Frequence"] = int(round(freq_hz))
        elif address == 62:  # Frequence_DDS (MSB)
            # Stockage temporaire MSB
            if not hasattr(self, '_freq_msb'):
                self._freq_msb = 0
            self._freq_msb = value
            # Calcul fréquence si LSB déjà reçu
            if hasattr(self, '_freq_lsb'):
                freq_uint32 = (self._freq_msb << 16) | self._freq_lsb
                freq_hz = self._uint32_to_freq(freq_uint32)
                self.memory_state["DDS"]["Frequence"] = int(round(freq_hz))
                
        # === DDS Modes ===
        elif address == 38:  # Mode DDS3+DDS4
            # Décoder les modes (voir manuel AD9106)
            mode_dds3 = "AC" if (value & 0xFF) == 12593 & 0xFF else "DC"
            mode_dds4 = "AC" if ((value >> 8) & 0xFF) == (12593 >> 8) & 0xFF else "DC"
            self.memory_state["DDS"]["Mode"][3] = mode_dds3
            self.memory_state["DDS"]["Mode"][4] = mode_dds4
        elif address == 39:  # Mode DDS1+DDS2
            mode_dds1 = "AC" if (value & 0xFF) == 12593 & 0xFF else "DC"
            mode_dds2 = "AC" if ((value >> 8) & 0xFF) == (12593 >> 8) & 0xFF else "DC"
            self.memory_state["DDS"]["Mode"][1] = mode_dds1
            self.memory_state["DDS"]["Mode"][2] = mode_dds2
            
        # === DDS Offsets ===
        elif address == 34:  # DAC4DOF
            self.memory_state["DDS"]["Offset"][4] = value
        elif address == 35:  # DAC3DOF
            self.memory_state["DDS"]["Offset"][3] = value
        elif address == 36:  # DAC2DOF
            self.memory_state["DDS"]["Offset"][2] = value
        elif address == 37:  # DAC1DOF
            self.memory_state["DDS"]["Offset"][1] = value
            
        # === DDS Constants ===
        elif address == 49:  # Const_1
            self.memory_state["DDS"]["Const"][1] = value
        elif address == 48:  # Const_2
            self.memory_state["DDS"]["Const"][2] = value
        elif address == 47:  # Const_3
            self.memory_state["DDS"]["Const"][3] = value
        elif address == 46:  # Const_4
            self.memory_state["DDS"]["Const"][4] = value
            
        # === DDS Gains ===
        elif address == 53:  # Gain_1
            self.memory_state["DDS"]["Gain"][1] = value
        elif address == 52:  # Gain_2
            self.memory_state["DDS"]["Gain"][2] = value
        elif address == 51:  # Gain_3
            self.memory_state["DDS"]["Gain"][3] = value
        elif address == 50:  # Gain_4
            self.memory_state["DDS"]["Gain"][4] = value
            
        # === DDS Phases ===
        elif address == 67:  # Phase_1
            self.memory_state["DDS"]["Phase"][1] = value
        elif address == 66:  # Phase_2
            self.memory_state["DDS"]["Phase"][2] = value
        elif address == 65:  # Phase_3
            self.memory_state["DDS"]["Phase"][3] = value
        elif address == 64:  # Phase_4
            self.memory_state["DDS"]["Phase"][4] = value


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
            # print(f"[DEBUG SerialCommunicator] send_command FAILED: Port série non connecté")
            return False, "Port série non connecté"
        
        with self.lock:
            try:
                # S'assurer que la commande se termine par '*'
                if not command.endswith('*'):
                    command += '*'
                
                # print(f"[DEBUG SerialCommunicator] Sending command: '{command}' → Hardware")
                    
                # Envoyer la commande
                self.ser.write(command.encode())
                
                # Pour les commandes d'acquisition (m), protocole à deux lectures
                if command.startswith('m') and command[1:].replace('*', '').isdigit():
                    # Première lecture : confirmation (ex: "m=  127\n")
                    confirmation = self.ser.readline()
                    # print(f"[DEBUG SerialCommunicator] Acquisition confirmation: '{confirmation.decode('ascii', errors='ignore').rstrip()}'")
                    # Seconde lecture : les vraies données (ex: "3789\t3181\t3071\t3113\t1666\t1987\t2351\t2212\t\n")
                    data_response = self.ser.readline()
                    response_str = data_response.decode('ascii', errors='ignore').rstrip('\r\n')
                    # print(f"[DEBUG SerialCommunicator] Acquisition data: '{response_str[:50]}...' (truncated)")
                    return True, response_str
                else:
                    # Pour les autres commandes, une seule lecture
                    response = self.ser.readline()
                    response_str = response.decode('ascii', errors='ignore').rstrip('\r\n')
                    # print(f"[DEBUG SerialCommunicator] Hardware response: '{response_str}'")
                    return True, response_str
                
            except Exception as e:
                # print(f"[DEBUG SerialCommunicator] send_command ERROR: {str(e)}")
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
    
    def _uint32_to_freq(self, uint32_value):
        """Convertit une valeur 32 bits non signée en fréquence"""
        freq = uint32_value * 16_000_000 / (2**32)
        return freq
    
    def _decomposer_uint32(self, valeur_32bits):
        """Décompose un entier 32 bits en partie haute (16 bits MSB) et partie basse (16 bits LSB)"""
        if not (0 <= valeur_32bits <= 4294967295):
            return False, f"Valeur {valeur_32bits} hors de la plage uint32"
        
        partie_haute = (valeur_32bits >> 16) & 0xFFFF
        partie_basse = valeur_32bits & 0xFFFF
        
        return True, (partie_haute, partie_basse)

    def set_dds_frequency(self, freq):
        """Configure la fréquence des DDS"""
        # print(f"[DEBUG SerialCommunicator] set_dds_frequency: freq={freq} Hz")
        
        success, result = self._freq_to_uint32(freq)
        if not success:
            # print(f"[DEBUG SerialCommunicator] _freq_to_uint32 FAILED: {result}")
            return False, result
        valeur_32bits = result
        # print(f"[DEBUG SerialCommunicator] Freq converted to uint32: {valeur_32bits}")
        
        success, result = self._decomposer_uint32(valeur_32bits)
        if not success:
            # print(f"[DEBUG SerialCommunicator] _decomposer_uint32 FAILED: {result}")
            return False, result
        partie_haute, partie_basse = result
        # print(f"[DEBUG SerialCommunicator] Freq MSB={partie_haute}, LSB={partie_basse}")
        
        # Envoi MSB
        success, response = self.send_command(f"a{self.DDS_ADDRESSES['Frequency'][0]}")
        if not success:
            return False, f"Erreur lors de l'envoi de l'adresse MSB: {response}"
        success, response = self.send_command(f"d{partie_haute}")
        if not success:
            return False, f"Erreur lors de l'envoi de la valeur MSB: {response}"
        
        # Envoi LSB
        success, response = self.send_command(f"a{self.DDS_ADDRESSES['Frequency'][1]}")
        if not success:
            return False, f"Erreur lors de l'envoi de l'adresse LSB: {response}"
        success, response = self.send_command(f"d{partie_basse}")
        if not success:
            return False, f"Erreur lors de l'envoi de la valeur LSB: {response}"
        
        # MAJ mémoire
        self.memory_state["DDS"]["Frequence"] = freq
        # print(f"[DEBUG SerialCommunicator] set_dds_frequency SUCCESS: {freq} Hz configured")
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
        # print(f"[DEBUG SerialCommunicator] set_dds_gain: channel={channel}, value={value}")
        
        if not (1 <= channel <= 4) or not (0 <= value <= 16376):
            # print(f"[DEBUG SerialCommunicator] set_dds_gain FAILED: Paramètres invalides (ch={channel}, val={value})")
            return False, "Paramètres invalides"
        
        # Adresse selon le canal
        addr = self.DDS_ADDRESSES["Gain"][channel]
        # print(f"[DEBUG SerialCommunicator] DDS{channel} gain address: {addr}")
        
        success, response = self.send_command(f"a{addr}")
        if not success:
            return False, f"Erreur lors de l'envoi de l'adresse de gain: {response}"
        
        success, response = self.send_command(f"d{value}")
        if not success:
            return False, f"Erreur lors de l'envoi de la valeur de gain: {response}"
        
        # MAJ mémoire
        self.memory_state["DDS"]["Gain"][channel] = value
        # print(f"[DEBUG SerialCommunicator] set_dds_gain SUCCESS: DDS{channel} gain={value}")
        
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
        # print(f"[DEBUG SerialCommunicator] set_dds_phase: channel={channel}, value={value}")
        
        if not (1 <= channel <= 4) or not (0 <= value <= 65535):
            # print(f"[DEBUG SerialCommunicator] set_dds_phase FAILED: Paramètres invalides (ch={channel}, val={value})")
            return False, "Paramètres invalides"
        
        # Adresse selon le canal
        addr = self.DDS_ADDRESSES["Phase"][channel]
        # print(f"[DEBUG SerialCommunicator] DDS{channel} phase address: {addr}")
        
        success, response = self.send_command(f"a{addr}")
        if not success:
            return False, f"Erreur lors de l'envoi de l'adresse de phase: {response}"
        
        success, response = self.send_command(f"d{value}")
        if not success:
            return False, f"Erreur lors de l'envoi de la valeur de phase: {response}"
        
        # MAJ mémoire
        self.memory_state["DDS"]["Phase"][channel] = value
        # print(f"[DEBUG SerialCommunicator] set_dds_phase SUCCESS: DDS{channel} phase={value}")
        
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
        # print(f"[DEBUG SerialCommunicator] set_adc_gain: channel={channel}, value={value}")
        
        if not (1 <= channel <= 4) or value not in [1, 2, 4, 8, 16]:
            # print(f"[DEBUG SerialCommunicator] set_adc_gain FAILED: Paramètres invalides (ch={channel}, val={value})")
            return False, "Paramètres invalides"
        
        # Adresse selon le canal et correspondance des valeurs
        addresses = {1: 17, 2: 18, 3: 19, 4: 20}
        gains_values = {1: 0, 2: 1, 4: 2, 8: 3, 16: 4}  # Conversion gain -> valeur à envoyer
        
        addr = addresses.get(channel)
        value_to_send = gains_values.get(value, 0)  # Valeur par défaut: 0 (gain de 1)
        # print(f"[DEBUG SerialCommunicator] ADC{channel} gain address={addr}, value_to_send={value_to_send} (from gain={value})")
        
        success, response = self.send_command(f"a{addr}")
        if not success:
            return False, f"Erreur lors de l'envoi de l'adresse de gain ADC: {response}"
        
        success, response = self.send_command(f"d{value_to_send}")
        if not success:
            return False, f"Erreur lors de l'envoi de la valeur de gain ADC: {response}"
        
        # MAJ mémoire
        self.memory_state["ADC"]["Gain"][channel] = value
        # print(f"[DEBUG SerialCommunicator] set_adc_gain SUCCESS: ADC{channel} gain={value}")
        
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
        # print(f"[DEBUG SerialCommunicator] set_clkin_divider: value={value}")
        
        if value not in [0, 2, 4, 6, 8, 10, 12, 14]:
            # print(f"[DEBUG SerialCommunicator] set_clkin_divider FAILED: Valeur invalide ({value})")
            return False, "Valeur invalide"
        
        # Conversion en code
        code_value = self._clkin_value_to_code(value)
        # print(f"[DEBUG SerialCommunicator] CLKIN divider: value={value} → code={code_value}")
        
        self.send_command(f"a13")
        self.send_command(f"d{code_value}")
        
        # MAJ mémoire
        self.memory_state["ADC"]["CLKIN_divider_ratio"] = value
        # print(f"[DEBUG SerialCommunicator] set_clkin_divider SUCCESS: {value} (code: {code_value})")
        
        return True, f"CLKIN divider ratio configuré à {value} (code: {code_value})"
    
    def set_iclk_divider_and_oversampling(self, iclk_value, oversampling_value):
        """
        Configure conjointement ICLK divider ratio et Oversampling ratio.

        Gherkin Specification:
        Feature: ADC Clock and Sampling Rate Configuration
            Context: Global acquisition system for Electric Field Imaging (AEFI)
            Hardware: ADS131A04 (ADC) coupled with AD9106 (DDS)
            
            As a hardware controller
            I need to set the ICLK divider and Oversampling ratio simultaneously
            Because they share the same hardware register (Address 14)
            
        Scenario: Configure ADC Timing Registers
            Given the serial communication is established with the board
            When the user requests to set:
                - iclk_value (Input Clock Divider)
                - oversampling_value (OSR)
            Then the input values are validated against hardware constraints:
                - iclk_value must be one of [0, 2, 4, 6, 8, 10, 12, 14]
                - oversampling_value must be a valid OSR (e.g., 4096, 2048, ..., 32)
            And the values are encoded into hardware-specific bitfields:
                - iclk_code (3 bits)
                - oversampling_code (4 bits)
            And the combined register value is calculated:
                - Formula: (iclk_code * 32) + oversampling_code
                  (Note: 32 corresponds to a 5-bit shift, placing ICLK in the upper bits of the byte)
            And the command sequence is sent over serial:
                1. "a14" (Select Register 14)
                2. "d{combined_value}" (Write Data)
            And the internal memory state is updated to reflect the new configuration
        """
        # print(f"[DEBUG SerialCommunicator] set_iclk_divider_and_oversampling: iclk={iclk_value}, oversampling={oversampling_value}")
        
        if iclk_value not in [0, 2, 4, 6, 8, 10, 12, 14]:
            # print(f"[DEBUG SerialCommunicator] set_iclk_divider_and_oversampling FAILED: Valeur ICLK invalide ({iclk_value})")
            return False, "Valeur ICLK invalide"
            
        valid_oversampling_values = [4096, 2048, 1024, 800, 768, 512, 400, 384, 256, 200, 192, 128, 96, 64, 48, 32]
        if oversampling_value not in valid_oversampling_values:
            # print(f"[DEBUG SerialCommunicator] set_iclk_divider_and_oversampling FAILED: Valeur Oversampling invalide ({oversampling_value})")
            return False, "Valeur Oversampling invalide"
        
        # Conversion en codes
        iclk_code = self._iclk_value_to_code(iclk_value)
        oversampling_code = self._oversampling_value_to_code(oversampling_value)
        
        # Calcul de la valeur combinée : iclk_code * 32 + oversampling_code
        combined_value = (iclk_code * 32) + oversampling_code
        # print(f"[DEBUG SerialCommunicator] ICLK+Oversampling: iclk_code={iclk_code}, oversamp_code={oversampling_code}, combined={combined_value}")
        
        self.send_command(f"a14")
        self.send_command(f"d{combined_value}")
        
        # MAJ mémoire
        self.memory_state["ADC"]["ICLK_divider_ratio"] = iclk_value
        self.memory_state["ADC"]["Oversampling_ratio"] = oversampling_value
        # print(f"[DEBUG SerialCommunicator] set_iclk_divider_and_oversampling SUCCESS: ICLK={iclk_value}, Oversampling={oversampling_value}")
        
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
        # print(f"[DEBUG SerialCommunicator] set_reference_config: neg_ref={negative_ref}, high_res={high_res}, ref_voltage={ref_voltage}, ref_selection={ref_selection}")
        
        val_combinee = 0
        
        # Negative reference (bit 7)
        if negative_ref:
            val_combinee += 128
            # print(f"[DEBUG SerialCommunicator] Negative ref enabled: +128")
            
        # High resolution (bit 6)
        if high_res:
            val_combinee += 64
            # print(f"[DEBUG SerialCommunicator] High resolution enabled: +64")
            
        # Reference voltage (0=2.442V, 1=4.0V)
        if ref_voltage == 1:
            val_combinee += 16
            # print(f"[DEBUG SerialCommunicator] Reference voltage 4.0V: +16")
            
        # Reference selection (0=External, 1=Internal)
        if ref_selection == 1:
            val_combinee += 8
            # print(f"[DEBUG SerialCommunicator] Internal reference: +8")
        
        # print(f"[DEBUG SerialCommunicator] ADC reference combined value: {val_combinee}")
        
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
        # print(f"[DEBUG SerialCommunicator] set_reference_config SUCCESS: valeur={val_combinee}")
        
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
