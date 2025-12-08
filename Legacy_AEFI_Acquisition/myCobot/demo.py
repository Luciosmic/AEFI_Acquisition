from pymycobot.mycobot import MyCobot
import time

# Initialiser MyCobot - Remplacez 'COM3' par votre port série réel et 115200 par le baud rate approprié
mc = MyCobot("COM9", 115200)

print("Début du script de test pour myCobot.")
try:
    i = 2
    while i > 0:
        print(f"Essai {8-i}: Allumage bleu")
        mc.set_color(0, 0, 255)  # Bleu
        time.sleep(2)
        print(f"Essai {8-i}: Allumage rouge")
        mc.set_color(255, 0, 0)  # Rouge
        time.sleep(2)
        print(f"Essai {8-i}: Allumage vert")
        mc.set_color(0, 255, 0)  # Vert
        time.sleep(2)
        i -= 1
    print("Fin des tests RGB. Début des tests de mouvement.")

    # Exemple de mouvement : Aller à la position zéro (tous les joints à 0)
    print("Mouvement vers position zéro...")
    mc.send_angles([0, 0, 0, 0, 0, 0], 50)  # Angles en degrés, vitesse 50
    time.sleep(3)  # Attendre 3 secondes pour que le mouvement se termine

    # Vérifier la position actuelle
    current_angles = mc.get_angles()
    print(f"Angles actuels : {current_angles}")

    # Mouvement vers une autre position (ex. : lever un joint)
    print("Mouvement vers une position personnalisée...")
    mc.send_angles([0, 30, 0, +30, 0, 0], 50)  # Ajuste les angles selon tes besoins
    time.sleep(3)
    mc.set_angles([0, 30, 0, +45, 0, 0], 50)
    # Retour à zéro
    print("Retour à position zéro...")
    mc.send_angles([0, 0, 0, 0, 0, 0], 50)
    time.sleep(3)

    print("Tests de mouvement terminés.")
except Exception as e:
    print(f"Erreur pendant l'exécution: {e}")

