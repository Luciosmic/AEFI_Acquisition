import serial
import time
import csv
from datetime import datetime

# Paramètres du port série
PORT = 'COM10'
BAUDRATE = 1500000
TIMEOUT = 10

# Fichier CSV de sortie
CSV_FILE = 'electric_field_data.csv'

# Demander à l'utilisateur la valeur de m
while True:
    try:
        m = int(input("Entrez la valeur de m (1-127) : "))
        if 1 <= m <= 1270:
            break
        else:
            print("Veuillez entrer un nombre entre 1 et 127.")
    except ValueError:
        print("Entrée invalide. Veuillez entrer un nombre entier.")

# Ouvrir le port série
ser = serial.Serial(
    port=PORT,
    baudrate=BAUDRATE,
    bytesize=8,
    stopbits=serial.STOPBITS_ONE,
    parity=serial.PARITY_NONE,
    timeout=TIMEOUT
)

# Ouvrir le fichier CSV en mode ajout
with open(CSV_FILE, mode='a', newline='') as csvfile:
    writer = csv.writer(csvfile)
    # Écrire l'en-tête si le fichier est vide
    if csvfile.tell() == 0:
        writer.writerow(['timestamp', 'x_imag', 'y_imag', 'y_reel', 'x_reel', 'z_imag', 'z_reel', 'val7', 'val8'])
    try:
        print("Acquisition en cours... (Ctrl+C pour arrêter)")
        while True:
            # Envoi de la commande
            command = f"m{m}*"
            ser.write(command.encode())
            # Lecture r1 (accusé de réception)
            r1 = ser.readline().decode(errors='ignore').strip()
            # Lecture r2 (données)
            r2 = ser.readline().decode(errors='ignore').strip()
            valeurs = r2.split('\t')
            if len(valeurs) >= 8:
                # Extraction des 6 premières valeurs + les 2 suivantes
                x_imag = int(valeurs[0])
                y_imag = int(valeurs[1])
                y_reel = int(valeurs[2])
                x_reel = int(valeurs[3])
                z_imag = int(valeurs[4])
                z_reel = int(valeurs[5])
                val7 = valeurs[6]
                val8 = valeurs[7]
                # Timestamp
                ts = datetime.now().isoformat()
                # Écriture dans le CSV
                writer.writerow([ts, x_imag, y_imag, y_reel, x_reel, z_imag, z_reel, val7, val8])
                csvfile.flush()
                # Affichage console
                print(f"{ts} | X imag: {x_imag}, Y imag: {y_imag}, Y réel: {y_reel}, X réel: {x_reel}, Z imag: {z_imag}, Z réel: {z_reel}")
            else:
                print(f"Réponse incomplète ou invalide : {r2}")
            time.sleep(0.1)  # Petite pause pour éviter de saturer
    except KeyboardInterrupt:
        print("\nAcquisition arrêtée par l'utilisateur.")
    finally:
        ser.write("S*".encode())  # Arrêt propre
        ser.close()
        print("Port série fermé.") 