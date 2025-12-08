import serial
import time

# Configuration du port série avec les paramètres identifiés
ser = serial.Serial(
    port='COM10',
    baudrate=1500000,
    bytesize=8,
    stopbits=serial.STOPBITS_ONE,  # Utiliser ONE même si la valeur est 10
    parity=serial.PARITY_NONE,
    timeout=10  # timeout en secondes
)

try:
    # Vérifier que le port est ouvert
    if not ser.is_open:
        ser.open()
    
    # Envoi de la commande (par exemple m124*)
    command = "m124*"
    ser.write(command.encode())
    
    # Lecture de la réponse
    response = ser.readline().decode().strip()
    print(f"Réponse reçue: {response}")
    response = ser.readline().decode().strip()
    print(f"Réponse reçue: {response}")


    command = "a65*"
    ser.write(command.encode())
    # Lecture de la réponse
    response = ser.readline().decode().strip()
    print(f"Réponse reçue: {response}")
    
    
    
    command = "d10000*"
    ser.write(command.encode())
    # Lecture de la réponse
    response = ser.readline().decode().strip()
    print(f"Réponse reçue: {response}")

    # Fermeture propre avec S*
    ser.write("S*".encode())
    
finally:
    # Fermeture du port série
    ser.close()
    print("Port série fermé")