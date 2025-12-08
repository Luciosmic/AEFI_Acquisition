from pymycobot.mycobot import MyCobot
import time

# Initialiser MyCobot - Remplacez 'COM9' par votre port série réel si nécessaire
mc = MyCobot("COM9", 115200)

print("Script interactif pour changer la position X, Y, Z du myCobot.")
print("Entrez 'q' pour quitter à tout moment.")

try:
    while True:
        # Demander les coordonnées à l'utilisateur
        x_input = input("Entrez la nouvelle position X (en mm, ex: 160) : ")
        if x_input.lower() == 'q':
            break
        
        y_input = input("Entrez la nouvelle position Y (en mm, ex: 0) : ")
        if y_input.lower() == 'q':
            break
        
        z_input = input("Entrez la nouvelle position Z (en mm, ex: 160) : ")
        if z_input.lower() == 'q':
            break
        
        try:
            # Convertir en floats
            x = float(x_input)
            y = float(y_input)
            z = float(z_input)
            
            # Coordonnées complètes : [x, y, z, rx, ry, rz] avec rotations à 0
            coords = [x, y, z, 0, 0, 0]
            
            # Appliquer le mouvement (vitesse 50, mode 0 par défaut)
            print(f"Envoi des coordonnées : {coords}")
            mc.send_coords(coords, 50, 0)
            
            # Attendre que le mouvement se termine (ajustez le délai si needed)
            time.sleep(3)
            
            # Vérifier la position actuelle
            current_coords = mc.get_coords()
            print(f"Position actuelle après mouvement : {current_coords}")
        
        except ValueError:
            print("Erreur : Veuillez entrer des nombres valides.")
        
        except Exception as e:
            print(f"Erreur pendant le mouvement : {e}")

except Exception as e:
    print(f"Erreur générale : {e}")

finally:
    # Retour à une position sûre (zéro) avant de quitter
    print("Retour à la position zéro pour sécurité...")
    mc.send_angles([0, 0, 0, 0, 0, 0], 50)
    time.sleep(3)
    print("Script terminé.")