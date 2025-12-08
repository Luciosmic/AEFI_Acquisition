#!/usr/bin/env python3
"""
Module de communication avec la carte DDS/ADC
Sépare la logique de communication de l'interface graphique

Note: Les paramètres et adresses matérielles sont documentés dans le fichier
ADC_DDS_Configuration_Parameters.json. Ce fichier contient la documentation
technique complète et à jour des adresses et paramètres du matériel.
"""

import serial
import time
import json
import os
from threading import Thread, Lock
from queue import Queue, Empty

# Adresses matérielles des DDS (validées par tests)
# Ces adresses sont documentées en détail dans ADC_DDS_Configuration_Parameters.json
DDS_ADDRESSES = {
    "Frequency": [62, 63],   # 62: MSB, 63: LSB
    "Mode": 39,              # Mode combiné pour DDS1 et DDS2
    "Gain": {1: 53, 2: 52},  # Gain DDS1: 53, Gain DDS2: 52
    "Offset": {1: 37, 2: 36},  # Offset DDS1: 37, Offset DDS2: 36
    "Phase": {1: 67, 2: 66},    # Phase DDS1: 67, Phase DDS2: 66
    "Const": {1: 49, 2: 48}     # Constante DDS1: 49, Constante DDS2: 48
}

# Valeurs des modes DDS
DDS_MODES = {
    1: {"AC": 49, "DC": 1},          # DDS1: AC = 49, DC = 1
    2: {"AC": 12544, "DC": 256}      # DDS2: AC = 12544, DC = 256
}

class SerialCommunicator:
    """Classe gérant la communication série avec la carte DDS/ADC"""
    
    def __init__(self, port=None, baudrate=1500000, config_file="ADC_DDS_Configuration_Parameters.json"):
        self.port = port
        self.baudrate = baudrate
        self.config_file = config_file
        self.ser = None
        
        # Configuration et paramètres
        self.config = {}
        self.load_config()
        
        # Variables pour la communication
        self.lock = Lock()
    
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
                
            # Ouvrir une nouvelle connexion
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=8,
                stopbits=serial.STOPBITS_ONE,
                parity=serial.PARITY_NONE,
                timeout=1
            )
            
            return True, "Connexion établie"
        except Exception as e:
            return False, f"Erreur de connexion: {str(e)}"
    
    def disconnect(self):
        """Ferme la connexion série"""
        if self.ser and self.ser.is_open:
            self.ser.close()
    
    def send_command(self, command):
        """Envoie une commande à la carte et attend la réponse"""
        if not self.ser or not self.ser.is_open:
            return False, "Port série non connecté"
        
        with self.lock:
            try:
                # S'assurer que la commande se termine par '*'
                if not command.endswith('*'):
                    command += '*'
                    
                # Envoyer la commande
                self.ser.write(command.encode())
                
                # Attendre la réponse
                response = b""
                while True:
                    if self.ser.in_waiting > 0:
                        response += self.ser.read(self.ser.in_waiting)
                        if response:  # Si on a reçu une réponse, on sort
                            break
                    time.sleep(0.001)  # Petit délai pour ne pas surcharger le CPU
                
                return True, response.decode().strip()
                
            except Exception as e:
                return False, f"Erreur de communication: {str(e)}"
    
    def get_response(self, timeout=None):
        """Récupère la dernière réponse (maintenu pour compatibilité)"""
        return self.send_command("r")[1]
    
    def get_error(self, timeout=None):
        """Récupère la dernière erreur (maintenu pour compatibilité)"""
        return None  # Les erreurs sont maintenant retournées directement par send_command
    
    def load_config(self, filename=None):
        """Charge la configuration depuis un fichier JSON"""
        if filename:
            self.config_file = filename
            
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                return True, "Configuration chargée avec succès"
            else:
                return False, f"Fichier de configuration {self.config_file} non trouvé"
        except Exception as e:
            return False, f"Erreur lors du chargement de la configuration: {str(e)}"
    
    def save_config(self, filename=None):
        """Sauvegarde la configuration dans un fichier JSON"""
        if filename:
            self.config_file = filename
            
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True, "Configuration sauvegardée avec succès"
        except Exception as e:
            return False, f"Erreur lors de la sauvegarde: {str(e)}"
    
    # Fonctions de contrôle pour les différents paramètres
    
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
        
        # MSB
        success, response = self.send_command(f"a{DDS_ADDRESSES['Frequency'][0]}")
        if not success:
            return False, f"Erreur lors de l'envoi de l'adresse MSB: {response}"
        
        success, response = self.send_command(f"d{partie_haute}")
        if not success:
            return False, f"Erreur lors de l'envoi de la valeur MSB: {response}"
        
        # LSB
        success, response = self.send_command(f"a{DDS_ADDRESSES['Frequency'][1]}")
        if not success:
            return False, f"Erreur lors de l'envoi de l'adresse LSB: {response}"
        
        success, response = self.send_command(f"d{partie_basse}")
        if not success:
            return False, f"Erreur lors de l'envoi de la valeur LSB: {response}"
        
        # Mettre à jour la configuration
        if "DDS" in self.config and "Frequence_DDS" in self.config["DDS"]:
            self.config["DDS"]["Frequence_DDS"]["valeur"] = freq
        
        return True, f"Fréquence configurée à {freq} Hz"
    
    def set_dds_modes(self, dds1_ac, dds2_ac, dds3_ac, dds4_ac):
        """Configure les modes AC/DC des DDS"""
        mode1 = DDS_MODES[1]["AC"] if dds1_ac else DDS_MODES[1]["DC"]
        mode2 = DDS_MODES[2]["AC"] if dds2_ac else DDS_MODES[2]["DC"]
        
        # DDS1 et DDS2
        valeur_dds12 = mode1 + mode2
        
        # Envoyer les commandes
        success, response = self.send_command(f"a{DDS_ADDRESSES['Mode']}")
        if not success:
            return False, f"Erreur lors de l'envoi de l'adresse de mode: {response}"
        
        success, response = self.send_command(f"d{valeur_dds12}")
        if not success:
            return False, f"Erreur lors de l'envoi de la valeur de mode: {response}"
        
        # Mettre à jour la configuration
        if "DDS" in self.config:
            if "Mode_1" in self.config["DDS"]:
                self.config["DDS"]["Mode_1"]["valeur"] = mode1
            if "Mode_2" in self.config["DDS"]:
                self.config["DDS"]["Mode_2"]["valeur"] = mode2
        
        return True, "Modes DDS configurés"
    
    def set_dds_gain(self, channel, value):
        """Configure le gain d'un canal DDS"""
        if not (1 <= channel <= 2) or not (0 <= value <= 32768):
            return False, "Paramètres invalides"
        
        # Adresse selon le canal
        addr = DDS_ADDRESSES["Gain"][channel]
        
        success, response = self.send_command(f"a{addr}")
        if not success:
            return False, f"Erreur lors de l'envoi de l'adresse de gain: {response}"
        
        success, response = self.send_command(f"d{value}")
        if not success:
            return False, f"Erreur lors de l'envoi de la valeur de gain: {response}"
        
        # Mettre à jour la configuration
        if "DDS" in self.config:
            param_name = f"Gain_{channel}"
            if param_name in self.config["DDS"]:
                self.config["DDS"][param_name]["valeur"] = value
        
        return True, f"Gain DDS{channel} configuré à {value}"
    
    def set_dds_offset(self, channel, value):
        """Configure l'offset d'un canal DDS"""
        if not (1 <= channel <= 2) or not (0 <= value <= 65535):
            return False, "Paramètres invalides"
        
        # Adresse selon le canal
        addr = DDS_ADDRESSES["Offset"][channel]
        
        success, response = self.send_command(f"a{addr}")
        if not success:
            return False, f"Erreur lors de l'envoi de l'adresse d'offset: {response}"
        
        success, response = self.send_command(f"d{value}")
        if not success:
            return False, f"Erreur lors de l'envoi de la valeur d'offset: {response}"
        
        # Mettre à jour la configuration
        if "DDS" in self.config:
            param_name = f"Offset_{channel}"
            if param_name in self.config["DDS"]:
                self.config["DDS"][param_name]["valeur"] = value
        
        return True, f"Offset DDS{channel} configuré à {value}"
    
    def set_dds_phase(self, channel, value):
        """Configure la phase d'un canal DDS"""
        if not (1 <= channel <= 2) or not (0 <= value <= 65535):
            return False, "Paramètres invalides"
        
        # Adresse selon le canal
        addr = DDS_ADDRESSES["Phase"][channel]
        
        success, response = self.send_command(f"a{addr}")
        if not success:
            return False, f"Erreur lors de l'envoi de l'adresse de phase: {response}"
        
        success, response = self.send_command(f"d{value}")
        if not success:
            return False, f"Erreur lors de l'envoi de la valeur de phase: {response}"
        
        # Mettre à jour la configuration
        if "DDS" in self.config:
            param_name = f"Phase_{channel}"
            if param_name in self.config["DDS"]:
                self.config["DDS"][param_name]["valeur"] = value
        
        return True, f"Phase DDS{channel} configurée à {value}"
    
    def set_dds_const(self, channel, value):
        """Configure la constante DC d'un canal DDS"""
        if not (1 <= channel <= 2) or not (0 <= value <= 65535):
            return False, "Paramètres invalides"
        
        # Adresse selon le canal
        addr = DDS_ADDRESSES["Const"][channel]
        
        success, response = self.send_command(f"a{addr}")
        if not success:
            return False, f"Erreur lors de l'envoi de l'adresse de constante: {response}"
        
        success, response = self.send_command(f"d{value}")
        if not success:
            return False, f"Erreur lors de l'envoi de la valeur de constante: {response}"
        
        # Mettre à jour la configuration
        if "DDS" in self.config:
            param_name = f"Const_{channel}"
            if param_name in self.config["DDS"]:
                self.config["DDS"][param_name]["valeur"] = value
        
        return True, f"Constante DC DDS{channel} configurée à {value}"
    
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
        
        # Mettre à jour la configuration
        if "ADC" in self.config:
            param_name = f"Gain_ADC_{channel}"
            if param_name in self.config["ADC"]:
                self.config["ADC"][param_name]["valeur"] = value
        
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
        
        # Mettre à jour la configuration
        if "ADC" in self.config and "CLKIN_divider_ratio" in self.config["ADC"]:
            self.config["ADC"]["CLKIN_divider_ratio"]["valeur"] = value
        
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
        
        # Mettre à jour la configuration
        if "ADC" in self.config:
            if "ICLK_divider_ratio" in self.config["ADC"]:
                self.config["ADC"]["ICLK_divider_ratio"]["valeur"] = iclk_value
            if "Oversampling_ratio" in self.config["ADC"]:
                self.config["ADC"]["Oversampling_ratio"]["valeur"] = oversampling_value
        
        return True, f"ICLK divider ({iclk_value}) et Oversampling ratio ({oversampling_value}) configurés (code: {combined_value})"
    
    def set_iclk_divider(self, value):
        """Configure uniquement ICLK divider ratio en préservant l'Oversampling ratio existant"""
        if value not in [0, 2, 4, 6, 8, 10, 12, 14]:
            return False, "Valeur invalide"
        
        # Récupérer la valeur actuelle d'oversampling
        current_oversampling = 4096  # Valeur par défaut
        if "ADC" in self.config and "Oversampling_ratio" in self.config["ADC"]:
            current_oversampling = self.config["ADC"]["Oversampling_ratio"].get("valeur", 4096)
        
        # Appeler la méthode commune
        return self.set_iclk_divider_and_oversampling(value, current_oversampling)
    
    def set_oversampling_ratio(self, value):
        """Configure uniquement Oversampling ratio en préservant l'ICLK divider ratio existant"""
        valid_values = [4096, 2048, 1024, 800, 768, 512, 400, 384, 256, 200, 192, 128, 96, 64, 48, 32]
        if value not in valid_values:
            return False, "Valeur invalide"
        
        # Récupérer la valeur actuelle de ICLK
        current_iclk = 2  # Valeur par défaut
        if "ADC" in self.config and "ICLK_divider_ratio" in self.config["ADC"]:
            current_iclk = self.config["ADC"]["ICLK_divider_ratio"].get("valeur", 2)
        
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
        
        # Mettre à jour la configuration
        if "ADC" in self.config and "References_Configuration" in self.config["ADC"]:
            ref_config = self.config["ADC"]["References_Configuration"]
            if "options" in ref_config:
                options = ref_config["options"]
                if "Negative_Reference" in options:
                    options["Negative_Reference"]["valeur"] = negative_ref
                if "High_Resolution" in options:
                    options["High_Resolution"]["valeur"] = high_res
                if "Reference_Voltage" in options:
                    options["Reference_Voltage"]["valeur"] = ref_voltage
                if "Reference_Selection" in options:
                    options["Reference_Selection"]["valeur"] = ref_selection
            ref_config["valeur"] = val_combinee
        
        return True, f"Références configurées (valeur: {val_combinee})"
    
    def set_point_origine(self, value):
        """Configure le point d'origine pour l'acquisition"""
        if not (0 <= value <= 65535):
            return False, "Valeur invalide"
        
        success, response = self.send_command(f"a70")
        if not success:
            return False, f"Erreur lors de l'envoi de l'adresse du point d'origine: {response}"
        
        success, response = self.send_command(f"d{value}")
        if not success:
            return False, f"Erreur lors de l'envoi de la valeur du point d'origine: {response}"
        
        # Mettre à jour la configuration
        if "ADC" in self.config and "Point_origine" in self.config["ADC"]:
            self.config["ADC"]["Point_origine"]["valeur"] = value
        
        return True, f"Point d'origine configuré à {value}"
    
    def set_nb_points(self, value):
        """Configure le nombre de points pour l'acquisition"""
        if not (0 <= value <= 65535):
            return False, "Valeur invalide"
        
        success, response = self.send_command(f"a71")
        if not success:
            return False, f"Erreur lors de l'envoi de l'adresse du nombre de points: {response}"
        
        success, response = self.send_command(f"d{value}")
        if not success:
            return False, f"Erreur lors de l'envoi de la valeur du nombre de points: {response}"
        
        # Mettre à jour la configuration
        if "ADC" in self.config and "Nb_points" in self.config["ADC"]:
            self.config["ADC"]["Nb_points"]["valeur"] = value
        
        return True, f"Nombre de points configuré à {value}"
    
    def set_mux(self, value):
        """Configure le multiplexeur pour les canaux (MUX_2X_3Z_4Y)"""
        if value not in [1, 2, 3, 4]:
            return False, "Valeur invalide"
        
        success, response = self.send_command(f"a72")
        if not success:
            return False, f"Erreur lors de l'envoi de l'adresse du multiplexeur: {response}"
        
        success, response = self.send_command(f"d{value}")
        if not success:
            return False, f"Erreur lors de l'envoi de la valeur du multiplexeur: {response}"
        
        # Mettre à jour la configuration
        if "ADC" in self.config and "Mux_2x_3Z_4Y" in self.config["ADC"]:
            self.config["ADC"]["Mux_2x_3Z_4Y"]["valeur"] = value
        
        return True, f"Multiplexeur configuré à {value}"
    
    def init_from_config(self):
        """Initialise tous les paramètres à partir de la configuration chargée"""
        if not self.config:
            return False, "Aucune configuration disponible"
        
        # Paramètres ADC
        for param_name, param_data in self.config.get("ADC", {}).items():
            if isinstance(param_data, dict) and "adresse" in param_data and "valeur" in param_data:
                adresse = param_data["adresse"]
                valeur = param_data["valeur"]
                
                # Cas spécial pour References_Configuration
                if param_name == "References_Configuration":
                    options = param_data.get("options", {})
                    negative_ref = options.get("Negative_Reference", {}).get("valeur", False)
                    high_res = options.get("High_Resolution", {}).get("valeur", True)
                    ref_voltage = options.get("Reference_Voltage", {}).get("valeur", 1)
                    ref_selection = options.get("Reference_Selection", {}).get("valeur", 1)
                    
                    self.set_reference_config(negative_ref, high_res, ref_voltage, ref_selection)
                    continue
                
                # Cas standard
                if isinstance(adresse, (int, str)):
                    self.send_command(f"a{adresse}")
                    self.send_command(f"d{valeur}")
        
        # Paramètres DDS
        for param_name, param_data in self.config.get("DDS", {}).items():
            if isinstance(param_data, dict) and "valeur" in param_data:
                # Cas spécial pour la fréquence DDS
                if param_name == "Frequence_DDS":
                    self.set_dds_frequency(param_data["valeur"])
                    continue
                    
                # Cas spécial pour les modes DDS (combinés à l'adresse 26 et 27)
                if param_name in ["Mode_1", "Mode_2", "Mode_3", "Mode_4"]:
                    continue  # Traités ci-dessous
                    
                # Cas standard
                if "adresse" in param_data:
                    adresse = param_data["adresse"]
                    valeur = param_data["valeur"]
                    
                    self.send_command(f"a{adresse}")
                    self.send_command(f"d{valeur}")
        
        # Configuration des modes DDS
        dds1_ac = self.config.get("DDS", {}).get("Mode_1", {}).get("valeur") == 49
        dds2_ac = self.config.get("DDS", {}).get("Mode_2", {}).get("valeur") == 12544
        dds3_ac = self.config.get("DDS", {}).get("Mode_3", {}).get("valeur") == 49
        dds4_ac = self.config.get("DDS", {}).get("Mode_4", {}).get("valeur") == 12544
        
        self.set_dds_modes(dds1_ac, dds2_ac, dds3_ac, dds4_ac)
        
        return True, "Initialisation terminée avec succès"
    
    def init_labview_config(self):
        """Initialise le système avec la configuration LabVIEW"""
        params_labview = [
            (13, 2), (14, 32), (17, 0), (18, 0), (19, 0), (20, 0),
            (63, 12583), (62, 8), (38, 12593), (39, 12593), (37, 0),
            (49, 0), (53, 2500), (67, 0), (36, 0), (48, 0), (52, 2500),
            (66, 0), (35, 0), (47, 0), (51, 10000), (65, 16384),
            (34, 0), (46, 0), (50, 10000), (64, 0)
        ]
        
        for adresse, valeur in params_labview:
            self.send_command(f"a{adresse}")
            self.send_command(f"d{valeur}")
        
        return True, "Initialisation LabVIEW terminée"


# Test du module si exécuté directement
if __name__ == "__main__":
    communicator = SerialCommunicator()
    
    # Exemple d'utilisation
    port = "COM10"  # À adapter
    if communicator.connect(port):
        print(f"Connecté à {port}")
        
        # Exemple : configurer la fréquence
        communicator.set_dds_frequency(1000)
        
        # Exemple : configurer les modes
        communicator.set_dds_modes(True, False, True, False)
        
        # Récupérer les réponses
        while not communicator.response_queue.empty():
            cmd, resp = communicator.get_response()
            print(f"Commande: {cmd} -> Réponse: {resp}")
        
        # Fermer la connexion
        communicator.disconnect()
    else:
        # Afficher les erreurs
        while not communicator.error_queue.empty():
            error = communicator.get_error()
            print(f"Erreur: {error}")
