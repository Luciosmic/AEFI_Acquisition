#!/usr/bin/env python3
"""
Script de test interactif pour le module AD9106/ADS131A04.
Permet de valider la communication et la configuration du banc via SerialCommunicator.
"""
import sys
from AD9106_ADS131A04_SerialCommunicationModule import SerialCommunicator

def afficher_etat(communicator):
    import pprint
    print("\n--- État mémoire logiciel du banc ---")
    pprint.pprint(communicator.get_memory_state())
    print("-------------------------------------\n")

def menu():
    print("\n" + "="*60)
    print("  MENU DE TEST AD9106/ADS131A04")
    print("="*60)
    print("1. Initialisation par défaut du banc")
    print("2. Régler la fréquence DDS")
    print("3. Régler les modes AC/DC des DDS (tous en même temps)")
    print("4. Régler un paramètre DDS (gain, offset, phase, constante)")
    print("5. Afficher l'état mémoire logiciel")
    print("6. Mode manuel (envoyer une commande brute)")
    print("7. Régler le mode AC/DC d'un DDS individuellement")
    print("0. Quitter")
    return input("\nVotre choix : ").strip()

def choisir_dds():
    while True:
        n = input("Numéro de DDS (1-4) : ").strip()
        if n in {"1", "2", "3", "4"}:
            return int(n)
        print("[ERREUR] Numéro invalide.")

def choisir_param():
    params = ["Gain", "Offset", "Phase", "Const"]
    print("Paramètres disponibles :", ", ".join(params))
    while True:
        p = input("Quel paramètre ? ").strip().capitalize()
        if p in params:
            return p
        print("[ERREUR] Paramètre invalide.")

def main():
    port = "COM10"  # À adapter si besoin
    communicator = SerialCommunicator()
    print(f"Connexion au port {port}...")
    success, msg = communicator.connect(port)
    if not success:
        print(f"[ERREUR] {msg}")
        sys.exit(1)
    print(f"[OK] {msg}")
    try:
        while True:
            choix = menu()
            if choix == "0":
                break
            elif choix == "1":
                ok, msg = communicator.init_default_config()
                print("[OK]" if ok else "[ERREUR]", msg)
            elif choix == "2":
                try:
                    freq = float(input("Fréquence en Hz : "))
                    ok, msg = communicator.set_dds_frequency(freq)
                    print("[OK]" if ok else "[ERREUR]", msg)
                except ValueError:
                    print("[ERREUR] Entrée invalide.")
            elif choix == "3":
                print("Entrez le mode pour chaque DDS (AC/DC)")
                modes = []
                for i in range(1, 5):
                    m = input(f"  DDS{i} (AC/DC) : ").strip().upper()
                    modes.append(m == "AC")
                ok, msg = communicator.set_dds_modes(*modes)
                print("[OK]" if ok else "[ERREUR]", msg)
            elif choix == "4":
                dds = choisir_dds()
                param = choisir_param()
                setter = {
                    "Gain": communicator.set_dds_gain,
                    "Offset": communicator.set_dds_offset,
                    "Phase": communicator.set_dds_phase,
                    "Const": communicator.set_dds_const
                }[param]
                val = input(f"Nouvelle valeur pour {param} DDS{dds} : ").strip()
                try:
                    val = int(val)
                    ok, msg = setter(dds, val)
                    print("[OK]" if ok else "[ERREUR]", msg)
                except ValueError:
                    print("[ERREUR] Valeur numérique invalide.")
            elif choix == "5":
                afficher_etat(communicator)
            elif choix == "6":
                print("Mode manuel : tapez une commande (ex: a39* ou d12593*) ou 'exit' pour sortir.")
                while True:
                    cmd = input(">> ").strip()
                    if cmd.lower() in {"exit", "quit", "q"}:
                        break
                    if cmd:
                        ok, rep = communicator.send_command(cmd)
                        print("[REPONSE]", rep if ok else f"[ERREUR] {rep}")
            elif choix == "7":
                dds = choisir_dds()
                mode = input(f"Nouveau mode pour DDS{dds} (AC/DC) : ").strip().upper()
                if mode not in {"AC", "DC"}:
                    print("[ERREUR] Mode invalide.")
                    continue
                setter = {
                    1: communicator.set_dds1_mode,
                    2: communicator.set_dds2_mode,
                    3: communicator.set_dds3_mode,
                    4: communicator.set_dds4_mode
                }[dds]
                setter(mode)
                print(f"[OK] Mode DDS{dds} réglé sur {mode}.")
            else:
                print("[ERREUR] Choix invalide.")
    finally:
        communicator.disconnect()
        print("\nPort série fermé. Fin du test.")

if __name__ == "__main__":
    main() 