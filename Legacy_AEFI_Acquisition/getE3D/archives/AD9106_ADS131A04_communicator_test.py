#!/usr/bin/env python3
"""
Script de vérification des paramètres DDS identifiés manuellement
Compare les valeurs attendues avec les réponses du matériel
"""
import serial
import time
import json

# Configuration du port série
ser = serial.Serial(
    port='COM10',
    baudrate=1500000,  # 1,5 Mbaud
    bytesize=8,
    stopbits=serial.STOPBITS_ONE,
    parity=serial.PARITY_NONE,
    timeout=1
)

# Paramètres DDS écrits en dur (issus du JSON)
PARAMS_DDS = {
    "Frequence_DDS": {"adresse": [62, 63], "valeur": 1000, "min": 0, "max": 4294967295},
    "Mode_1": {"adresse": 39, "valeur": 49, "options": [1, 49]},
    "Mode_2": {"adresse": 39, "valeur": 12544, "options": [256, 12544]},
    "Mode_3": {
        "adresse": 69,
        "adresse_hex": "0x45",
        "valeur": 2048,
        "valeur_hex": "0x800",
        "options": [
            {"valeur": 0, "valeur_hex": "0x000", "description": "Sinus DDS3 désactivé"},
            {"valeur": 2048, "valeur_hex": "0x800", "description": "Cosinus DDS3 activé (bit 11)"}
        ],
        "description": "Mode DDS3: Configuration via DDSx_CONFIG, bit 11 (DDS_COS_EN3). 0=sinus, 1=cosinus"
    },
    "Mode_4": {
        "adresse": 69,
        "adresse_hex": "0x45",
        "valeur": 32768,
        "valeur_hex": "0x8000",
        "options": [
            {"valeur": 0, "valeur_hex": "0x0000", "description": "Sinus DDS4 désactivé"},
            {"valeur": 32768, "valeur_hex": "0x8000", "description": "Cosinus DDS4 activé (bit 15)"}
        ],
        "description": "Mode DDS4: Configuration via DDSx_CONFIG, bit 15 (DDS_COS_EN4). 0=sinus, 1=cosinus"
    },
    "Offset_1": {"adresse": 37, "valeur": 0, "min": 0, "max": 65535},
    "Offset_2": {"adresse": 36, "valeur": 0, "min": 0, "max": 65535},
    "Offset_3": {"adresse": 38, "valeur": 0, "min": 0, "max": 65535},
    "Offset_4": {"adresse": 38, "valeur": 0, "min": 0, "max": 65535},
    "Gain_1": {"adresse": 53, "valeur": 16384, "min": 0, "max": 32768},
    "Gain_2": {"adresse": 52, "valeur": 16384, "min": 0, "max": 32768},
    "Gain_3": {"adresse": 51, "valeur": 16384, "min": 0, "max": 32768},
    "Gain_4": {"adresse": 50, "valeur": 16384, "min": 0, "max": 32768},
    "Phase_1": {"adresse": 67, "valeur": 0, "min": 0, "max": 65535},
    "Phase_2": {"adresse": 66, "valeur": 0, "min": 0, "max": 65535},
    "Phase_3": {"adresse": 65, "valeur": 0, "min": 0, "max": 65535},
    "Phase_4": {"adresse": 64, "valeur": 0, "min": 0, "max": 65535},
    "Const_1": {"adresse": 49, "valeur": 0, "min": 0, "max": 65535},
    "Const_2": {"adresse": 48, "valeur": 0, "min": 0, "max": 65535},
    "Const_3": {"adresse": 47, "valeur": 0, "min": 0, "max": 65535},
    "Const_4": {"adresse": 46, "valeur": 0, "min": 0, "max": 65535},
    "DDS_Cycles_3": {
        "adresse": 87,
        "adresse_hex": "0x57",
        "valeur": 1,
        "valeur_hex": "0x0001",
        "min": 0,
        "max": 65535,
        "description": "Nombre de cycles DDS pour DDS3. Registre DDS_CYC3, bits [15:0] pour DDS_CYC3"
    },
    "DDS_Cycles_4": {
        "adresse": 83,
        "adresse_hex": "0x53",
        "valeur": 1,
        "valeur_hex": "0x0001",
        "min": 0,
        "max": 65535,
        "description": "Nombre de cycles DDS pour DDS4. Registre DDS_CYC4, bits [15:0] pour DDS_CYC4"
    }
}
print("Clés présentes dans PARAMS_DDS :", list(PARAMS_DDS.keys()))

def charger_params_dds(json_path="../docs/ADC_DDS_Configuration_Parameters.json"):
    """Charge la section DDS du fichier JSON de configuration."""
    global PARAMS_DDS
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            PARAMS_DDS = data.get("DDS", {})
    except Exception as e:
        print(f"[ERREUR] Impossible de charger les paramètres DDS depuis {json_path} : {e}")
        PARAMS_DDS = {}

# Charger les paramètres DDS au démarrage
charger_params_dds()

def envoyer_recevoir(cmd):
    """Envoie une commande et attend la réponse"""
    if not cmd.endswith('*'):
        cmd += '*'
    
    try:
        # Envoyer la commande
        print(f"Envoi: {cmd}")
        ser.write(cmd.encode())
        ser.flush()
        
        # Lire la réponse
        reponse = ser.readline().decode().strip()
        print(f"Réponse: {reponse}")
        return True, reponse
        
    except Exception as e:
        print(f"Erreur: {str(e)}")
        return False, None

def regler_frequence(frequence_hz):
    """Règle la fréquence DDS"""
    print(f"\n=== Réglage de la fréquence à {frequence_hz} Hz ===")
    
    # Calculer la valeur 32 bits
    freq_value = int(frequence_hz * (2**32) / 16_000_000)
    msb = (freq_value >> 16) & 0xFFFF
    lsb = freq_value & 0xFFFF
    
    print(f"MSB (62): {msb}, LSB (63): {lsb}")
    
    # Configurer MSB
    success, _ = envoyer_recevoir(f"a62")
    if not success:
        return False
    success, _ = envoyer_recevoir(f"d{msb}")
    if not success:
        return False
        
    # Configurer LSB
    success, _ = envoyer_recevoir(f"a63")
    if not success:
        return False
    success, _ = envoyer_recevoir(f"d{lsb}")
    if not success:
        return False
    
    return True

def configurer_mode(mode_dds1, mode_dds2):
    """Configure les modes AC/DC des deux DDS"""
    mode_str1 = "AC" if mode_dds1 == "AC" else "DC"
    mode_str2 = "AC" if mode_dds2 == "AC" else "DC"
    
    print(f"\n=== Configuration des modes: DDS1 en {mode_str1}, DDS2 en {mode_str2} ===")
    
    # Déterminer les valeurs numériques
    val_dds1 = 49 if mode_dds1 == "AC" else 1
    val_dds2 = 12544 if mode_dds2 == "AC" else 256
    
    # Calculer la valeur combinée
    val_combinee = val_dds1 + val_dds2
    
    # Envoyer la configuration
    success, _ = envoyer_recevoir(f"a39")
    if not success:
        return False, None
    
    success, _ = envoyer_recevoir(f"d{val_combinee}")
    if not success:
        return False, None
    
    return True, val_combinee

def tester_gain(dds_num):
    """Teste le gain pour un DDS spécifique"""
    adresse = 53 if dds_num == 1 else 52
    print(f"\n=== Test du gain DDS{dds_num} (adresse {adresse}) ===")
    
    niveaux = [0, 8192, 16384, 24576, 32768]  # 0%, 25%, 50%, 75%, 100%
    pourcentages = ["0%", "25%", "50%", "75%", "100%"]
    
    for niveau, pourcentage in zip(niveaux, pourcentages):
        print(f"\nRéglage du gain à {pourcentage} ({niveau})")
        success, _ = envoyer_recevoir(f"a{adresse}")
        if not success:
            continue
            
        success, _ = envoyer_recevoir(f"d{niveau}")
        if not success:
            continue
        
        # Laisser le temps d'observer à l'oscilloscope
        input(f"Appuyez sur Entrée après avoir vérifié à l'oscilloscope...")
    
    # Remettre à 50%
    success, _ = envoyer_recevoir(f"a{adresse}")
    if success:
        envoyer_recevoir(f"d16384")

def tester_offset(dds_num):
    """Teste l'offset pour un DDS spécifique"""
    adresse = 37 if dds_num == 1 else 36
    print(f"\n=== Test de l'offset DDS{dds_num} (adresse {adresse}) ===")
    
    niveaux = [0, 16384, 32768, 49152, 65535]  # 0%, 25%, 50%, 75%, 100%
    pourcentages = ["0%", "25%", "50%", "75%", "100%"]
    
    for niveau, pourcentage in zip(niveaux, pourcentages):
        print(f"\nRéglage de l'offset à {pourcentage} ({niveau})")
        success, _ = envoyer_recevoir(f"a{adresse}")
        if not success:
            continue
            
        success, _ = envoyer_recevoir(f"d{niveau}")
        if not success:
            continue
        
        # Laisser le temps d'observer à l'oscilloscope
        input(f"Appuyez sur Entrée après avoir vérifié à l'oscilloscope...")
    
    # Remettre à 0%
    success, _ = envoyer_recevoir(f"a{adresse}")
    if success:
        envoyer_recevoir(f"d0")

def tester_phase(dds_num):
    """Teste la phase pour un DDS spécifique"""
    adresse = 67 if dds_num == 1 else 66
    print(f"\n=== Test de la phase DDS{dds_num} (adresse {adresse}) ===")
    
    phases = [0, 16384, 32768, 49152]  # 0°, 90°, 180°, 270°
    degres = ["0°", "90°", "180°", "270°"]
    
    for phase, degre in zip(phases, degres):
        print(f"\nRéglage de la phase à {degre} ({phase})")
        success, _ = envoyer_recevoir(f"a{adresse}")
        if not success:
            continue
            
        success, _ = envoyer_recevoir(f"d{phase}")
        if not success:
            continue
        
        # Laisser le temps d'observer à l'oscilloscope
        input(f"Appuyez sur Entrée après avoir vérifié à l'oscilloscope...")
    
    # Remettre à 0°
    success, _ = envoyer_recevoir(f"a{adresse}")
    if success:
        envoyer_recevoir(f"d0")

def tester_constante(dds_num):
    """Teste la constante DC pour un DDS spécifique (en mode DC)"""
    adresse = 49 if dds_num == 1 else 48
    print(f"\n=== Test de la constante DC DDS{dds_num} (adresse {adresse}) ===")
    
    # Configurer le mode DC pour le DDS en question
    if dds_num == 1:
        success, _ = configurer_mode("DC", "DC")  # Les deux en DC pour simplifier
    else:
        success, _ = configurer_mode("DC", "DC")  # Les deux en DC pour simplifier
        
    if not success:
        print("[ERREUR] Échec de la configuration du mode DC")
        return
    
    niveaux = [0, 16384, 32768, 49152, 65535]  # 0%, 25%, 50%, 75%, 100%
    pourcentages = ["0%", "25%", "50%", "75%", "100%"]
    
    for niveau, pourcentage in zip(niveaux, pourcentages):
        print(f"\nRéglage de la constante DC à {pourcentage} ({niveau})")
        success, _ = envoyer_recevoir(f"a{adresse}")
        if not success:
            continue
            
        success, _ = envoyer_recevoir(f"d{niveau}")
        if not success:
            continue
        
        # Laisser le temps d'observer à l'oscilloscope
        input(f"Appuyez sur Entrée après avoir vérifié à l'oscilloscope...")
    
    # Remettre à 50%
    success, _ = envoyer_recevoir(f"a{adresse}")
    if success:
        envoyer_recevoir(f"d32768")

def tester_interaction_mode_offset_constante():
    """Teste l'interaction entre mode, offset et constante"""
    print(f"\n=== Test de l'interaction entre mode, offset et constante ===")
    
    # Test sur DDS1
    print("\n--- DDS1 : Comportement de l'offset en mode AC et de la constante en mode DC ---")
    
    # 1. Mode AC, variation de l'offset
    success, _ = configurer_mode("AC", "DC")  # DDS1 en AC, DDS2 en DC
    if not success:
        print("[ERREUR] Échec de la configuration du mode AC")
        return
        
    print(f"\n1. DDS1 en mode AC - L'offset doit affecter la composante continue")
    
    # Initialiser le gain pour voir l'effet
    success, _ = envoyer_recevoir("a53")
    if not success:
        print("[ERREUR] Échec de la configuration de l'adresse du gain")
        return
        
    success, _ = envoyer_recevoir("d16384")  # Gain à 50%
    if not success:
        print("[ERREUR] Échec de la configuration de la valeur du gain")
        return
    
    niveaux = [0, 32768, 65535]  # 0%, 50%, 100%
    pourcentages = ["0%", "50%", "100%"]
    
    for niveau, pourcentage in zip(niveaux, pourcentages):
        print(f"\nRéglage de l'offset à {pourcentage} ({niveau})")
        success, _ = envoyer_recevoir("a37")
        if not success:
            continue
            
        success, _ = envoyer_recevoir(f"d{niveau}")
        if not success:
            continue
        
        # Laisser le temps d'observer à l'oscilloscope
        input(f"Appuyez sur Entrée après avoir vérifié l'effet de l'offset en mode AC...")
    
    # Remettre l'offset à 0
    success, _ = envoyer_recevoir("a37")
    if success:
        envoyer_recevoir("d0")
    
    # 2. Mode DC, variation de la constante
    success, _ = configurer_mode("DC", "DC")  # DDS1 en DC, DDS2 en DC
    if not success:
        print("[ERREUR] Échec de la configuration du mode DC")
        return
        
    print(f"\n2. DDS1 en mode DC - La constante doit déterminer le niveau DC")
    
    for niveau, pourcentage in zip(niveaux, pourcentages):
        print(f"\nRéglage de la constante à {pourcentage} ({niveau})")
        success, _ = envoyer_recevoir("a49")
        if not success:
            continue
            
        success, _ = envoyer_recevoir(f"d{niveau}")
        if not success:
            continue
        
        # Laisser le temps d'observer à l'oscilloscope
        input(f"Appuyez sur Entrée après avoir vérifié l'effet de la constante en mode DC...")
    
    # Remettre à une valeur moyenne
    success, _ = envoyer_recevoir("a49")
    if success:
        envoyer_recevoir("d32768")
    
    # 3. Effet de l'offset en mode DC
    print(f"\n3. DDS1 toujours en mode DC - L'offset ne devrait avoir aucun effet")
    
    for niveau, pourcentage in zip(niveaux, pourcentages):
        print(f"\nRéglage de l'offset à {pourcentage} ({niveau})")
        success, _ = envoyer_recevoir("a37")
        if not success:
            continue
            
        success, _ = envoyer_recevoir(f"d{niveau}")
        if not success:
            continue
        
        # Laisser le temps d'observer à l'oscilloscope
        input(f"Appuyez sur Entrée après avoir vérifié que l'offset n'a pas d'effet en mode DC...")
    
    # Nettoyer les paramètres
    success, _ = configurer_mode("AC", "AC")  # Remettre les deux en AC
    if not success:
        print("[ERREUR] Échec de la remise en mode AC")
        return
    
    # Initialiser les autres paramètres à des valeurs standard
    success, _ = envoyer_recevoir("a37")  # Offset DDS1
    if success:
        envoyer_recevoir("d0")
        
    success, _ = envoyer_recevoir("a36")  # Offset DDS2
    if success:
        envoyer_recevoir("d0")
        
    success, _ = envoyer_recevoir("a53")  # Gain DDS1
    if success:
        envoyer_recevoir("d16384")
        
    success, _ = envoyer_recevoir("a52")  # Gain DDS2
    if success:
        envoyer_recevoir("d16384")
        
    success, _ = envoyer_recevoir("a67")  # Phase DDS1
    if success:
        envoyer_recevoir("d0")
        
    success, _ = envoyer_recevoir("a66")  # Phase DDS2
    if success:
        envoyer_recevoir("d0")
    
    print(f"\n[OK] Test d'interaction terminé. Paramètres remis à des valeurs standard.")

def initialiser():
    """Initialise le système avec des paramètres de base"""
    print("Initialisation des paramètres de base...")
    
    # Fréquence 1000 Hz
    success = regler_frequence(1000)
    if not success:
        print("[ERREUR] Échec de l'initialisation de la fréquence")
        return False
    
    # Les deux DDS en mode AC
    success, _ = configurer_mode("AC", "AC")
    if not success:
        print("[ERREUR] Échec de l'initialisation des modes")
        return False
    
    # Gains à 50%
    success, _ = envoyer_recevoir("a53")
    if success:
        envoyer_recevoir("d16384")  # Gain DDS1
        
    success, _ = envoyer_recevoir("a52")
    if success:
        envoyer_recevoir("d16384")  # Gain DDS2
    
    # Offsets à 0
    success, _ = envoyer_recevoir("a37")
    if success:
        envoyer_recevoir("d0")  # Offset DDS1
        
    success, _ = envoyer_recevoir("a36")
    if success:
        envoyer_recevoir("d0")  # Offset DDS2
    
    # Phases à 0
    success, _ = envoyer_recevoir("a67")
    if success:
        envoyer_recevoir("d0")  # Phase DDS1
        
    success, _ = envoyer_recevoir("a66")
    if success:
        envoyer_recevoir("d0")  # Phase DDS2
    
    print("[OK] Initialisation terminée.")
    return True

def tester_gain_3():
    """Teste le gain pour DDS3"""
    param = PARAMS_DDS["Gain_3"]
    adresse = param["adresse"]
    print(f"\n=== Test du gain DDS3 (adresse {adresse}) ===")
    niveaux = [0, 8192, 16384, 24576, 32768]
    pourcentages = ["0%", "25%", "50%", "75%", "100%"]
    for niveau, pourcentage in zip(niveaux, pourcentages):
        print(f"\nRéglage du gain à {pourcentage} ({niveau})")
        success, _ = envoyer_recevoir(f"a{adresse}")
        if not success:
            continue
        success, _ = envoyer_recevoir(f"d{niveau}")
        if not success:
            continue
        input(f"Appuyez sur Entrée après avoir vérifié à l'oscilloscope...")
    success, _ = envoyer_recevoir(f"a{adresse}")
    if success:
        envoyer_recevoir(f"d16384")

def tester_gain_4():
    """Teste le gain pour DDS4"""
    param = PARAMS_DDS["Gain_4"]
    adresse = param["adresse"]
    print(f"\n=== Test du gain DDS4 (adresse {adresse}) ===")
    niveaux = [0, 8192, 16384, 24576, 32768]
    pourcentages = ["0%", "25%", "50%", "75%", "100%"]
    for niveau, pourcentage in zip(niveaux, pourcentages):
        print(f"\nRéglage du gain à {pourcentage} ({niveau})")
        success, _ = envoyer_recevoir(f"a{adresse}")
        if not success:
            continue
        success, _ = envoyer_recevoir(f"d{niveau}")
        if not success:
            continue
        input(f"Appuyez sur Entrée après avoir vérifié à l'oscilloscope...")
    success, _ = envoyer_recevoir(f"a{adresse}")
    if success:
        envoyer_recevoir(f"d16384")

def tester_offset_3():
    """Teste l'offset pour DDS3"""
    param = PARAMS_DDS["Offset_3"]
    adresse = param["adresse"]
    print(f"\n=== Test de l'offset DDS3 (adresse {adresse}) ===")
    niveaux = [0, 16384, 32768, 49152, 65535]
    pourcentages = ["0%", "25%", "50%", "75%", "100%"]
    for niveau, pourcentage in zip(niveaux, pourcentages):
        print(f"\nRéglage de l'offset à {pourcentage} ({niveau})")
        success, _ = envoyer_recevoir(f"a{adresse}")
        if not success:
            continue
        success, _ = envoyer_recevoir(f"d{niveau}")
        if not success:
            continue
        input(f"Appuyez sur Entrée après avoir vérifié à l'oscilloscope...")
    success, _ = envoyer_recevoir(f"a{adresse}")
    if success:
        envoyer_recevoir(f"d0")

def tester_offset_4():
    """Teste l'offset pour DDS4"""
    param = PARAMS_DDS["Offset_4"]
    adresse = param["adresse"]
    print(f"\n=== Test de l'offset DDS4 (adresse {adresse}) ===")
    niveaux = [0, 16384, 32768, 49152, 65535]
    pourcentages = ["0%", "25%", "50%", "75%", "100%"]
    for niveau, pourcentage in zip(niveaux, pourcentages):
        print(f"\nRéglage de l'offset à {pourcentage} ({niveau})")
        success, _ = envoyer_recevoir(f"a{adresse}")
        if not success:
            continue
        success, _ = envoyer_recevoir(f"d{niveau}")
        if not success:
            continue
        input(f"Appuyez sur Entrée après avoir vérifié à l'oscilloscope...")
    success, _ = envoyer_recevoir(f"a{adresse}")
    if success:
        envoyer_recevoir(f"d0")

def tester_phase_3():
    """Teste la phase pour DDS3"""
    param = PARAMS_DDS["Phase_3"]
    adresse = param["adresse"]
    print(f"\n=== Test de la phase DDS3 (adresse {adresse}) ===")
    phases = [0, 16384, 32768, 49152]
    degres = ["0°", "90°", "180°", "270°"]
    for phase, degre in zip(phases, degres):
        print(f"\nRéglage de la phase à {degre} ({phase})")
        success, _ = envoyer_recevoir(f"a{adresse}")
        if not success:
            continue
        success, _ = envoyer_recevoir(f"d{phase}")
        if not success:
            continue
        input(f"Appuyez sur Entrée après avoir vérifié à l'oscilloscope...")
    success, _ = envoyer_recevoir(f"a{adresse}")
    if success:
        envoyer_recevoir(f"d0")

def tester_phase_4():
    """Teste la phase pour DDS4"""
    param = PARAMS_DDS["Phase_4"]
    adresse = param["adresse"]
    print(f"\n=== Test de la phase DDS4 (adresse {adresse}) ===")
    phases = [0, 16384, 32768, 49152]
    degres = ["0°", "90°", "180°", "270°"]
    for phase, degre in zip(phases, degres):
        print(f"\nRéglage de la phase à {degre} ({phase})")
        success, _ = envoyer_recevoir(f"a{adresse}")
        if not success:
            continue
        success, _ = envoyer_recevoir(f"d{phase}")
        if not success:
            continue
        input(f"Appuyez sur Entrée après avoir vérifié à l'oscilloscope...")
    success, _ = envoyer_recevoir(f"a{adresse}")
    if success:
        envoyer_recevoir(f"d0")

def tester_constante_3():
    """Teste la constante DC pour DDS3"""
    param = PARAMS_DDS["Const_3"]
    adresse = param["adresse"]
    print(f"\n=== Test de la constante DC DDS3 (adresse {adresse}) ===")
    niveaux = [0, 16384, 32768, 49152, 65535]
    pourcentages = ["0%", "25%", "50%", "75%", "100%"]
    for niveau, pourcentage in zip(niveaux, pourcentages):
        print(f"\nRéglage de la constante DC à {pourcentage} ({niveau})")
        success, _ = envoyer_recevoir(f"a{adresse}")
        if not success:
            continue
        success, _ = envoyer_recevoir(f"d{niveau}")
        if not success:
            continue
        input(f"Appuyez sur Entrée après avoir vérifié à l'oscilloscope...")
    success, _ = envoyer_recevoir(f"a{adresse}")
    if success:
        envoyer_recevoir(f"d32768")

def tester_constante_4():
    """Teste la constante DC pour DDS4"""
    param = PARAMS_DDS["Const_4"]
    adresse = param["adresse"]
    print(f"\n=== Test de la constante DC DDS4 (adresse {adresse}) ===")
    niveaux = [0, 16384, 32768, 49152, 65535]
    pourcentages = ["0%", "25%", "50%", "75%", "100%"]
    for niveau, pourcentage in zip(niveaux, pourcentages):
        print(f"\nRéglage de la constante DC à {pourcentage} ({niveau})")
        success, _ = envoyer_recevoir(f"a{adresse}")
        if not success:
            continue
        success, _ = envoyer_recevoir(f"d{niveau}")
        if not success:
            continue
        input(f"Appuyez sur Entrée après avoir vérifié à l'oscilloscope...")
    success, _ = envoyer_recevoir(f"a{adresse}")
    if success:
        envoyer_recevoir(f"d32768")

def menu_principal():
    """Menu principal interactif"""
    while True:
        print("\n============================================")
        print("     VÉRIFICATION DES PARAMÈTRES DDS")
        print("============================================")
        print("1. Configurer la fréquence")
        print("2. Configurer les modes (AC/DC)")
        print("3. Tester le gain DDS1")
        print("4. Tester le gain DDS2")
        print("5. Tester le gain DDS3")
        print("6. Tester le gain DDS4")
        print("7. Tester l'offset DDS1")
        print("8. Tester l'offset DDS2")
        print("9. Tester l'offset DDS3")
        print("10. Tester l'offset DDS4")
        print("11. Tester la phase DDS1")
        print("12. Tester la phase DDS2")
        print("13. Tester la phase DDS3")
        print("14. Tester la phase DDS4")
        print("15. Tester la constante DC DDS1")
        print("16. Tester la constante DC DDS2")
        print("17. Tester la constante DC DDS3")
        print("18. Tester la constante DC DDS4")
        print("19. Tester l'interaction mode/offset/constante (DDS1/DDS2)")
        print("20. Envoyer une commande personnalisée")
        print("0. Quitter")
        choix = input("\nVotre choix: ")
        if choix == "0":
            break
        elif choix == "1":
            try:
                freq = float(input("Fréquence en Hz: "))
                regler_frequence(freq)
            except ValueError:
                print("[ERREUR] Fréquence invalide")
        elif choix == "2":
            mode1 = input("Mode DDS1 (AC/DC): ").upper()
            mode2 = input("Mode DDS2 (AC/DC): ").upper()
            if mode1 in ["AC", "DC"] and mode2 in ["AC", "DC"]:
                configurer_mode(mode1, mode2)
            else:
                print("[ERREUR] Modes invalides. Utilisez AC ou DC.")
        elif choix == "3":
            tester_gain(1)
        elif choix == "4":
            tester_gain(2)
        elif choix == "5":
            tester_gain_3()
        elif choix == "6":
            tester_gain_4()
        elif choix == "7":
            tester_offset(1)
        elif choix == "8":
            tester_offset(2)
        elif choix == "9":
            tester_offset_3()
        elif choix == "10":
            tester_offset_4()
        elif choix == "11":
            tester_phase(1)
        elif choix == "12":
            tester_phase(2)
        elif choix == "13":
            tester_phase_3()
        elif choix == "14":
            tester_phase_4()
        elif choix == "15":
            tester_constante(1)
        elif choix == "16":
            tester_constante(2)
        elif choix == "17":
            tester_constante_3()
        elif choix == "18":
            tester_constante_4()
        elif choix == "19":
            tester_interaction_mode_offset_constante()
        elif choix == "20":
            print("Mode console interactif. Tapez 'exit' ou 'q' pour quitter.")
            while True:
                cmd = input("Commande à envoyer: ").strip()
                if cmd.lower() in ["exit", "q", "quit"]:
                    print("Sortie du mode console.")
                    break
                if cmd:
                    envoyer_recevoir(cmd)
        else:
            print("[ERREUR] Choix invalide")

# Programme principal
try:
    # Vérifier que le port est ouvert
    if not ser.is_open:
        ser.open()
    
    print("Connexion établie sur COM10 à 1500000 bauds")
    
    # Initialiser le système
    initialiser()
    
    # Afficher le menu
    menu_principal()
    
except Exception as e:
    print(f"[ERREUR] {e}")
finally:
    # Fermeture du port série
    if 'ser' in locals() and ser.is_open:
        ser.close()
    print("Port série fermé") 