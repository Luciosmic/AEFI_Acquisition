"""
Script de validation des profils de vitesse pour synchronisation avec acquisition continue.
Test les phases d'acceleration, vitesse constante et deceleration pour correlation temporelle.
"""

import sys
import os
import time
import threading
import matplotlib.pyplot as plt
import numpy as np
import csv
from datetime import datetime

# Import du controleur
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
from ArcusPerformaxPythonController.controller.ArcusPerformax4EXStage_Controller import EFImagingStageController

# Parametres
DLL_PATH = r"C:/Users/manip/Dropbox/Luis/1 PROJETS/1 - THESE/Ressources/ExperimentalData_ASSOCE/Dev/ArcusPerformaxPythonController/controller/DLL64"

class VelocityProfileAnalyzer:
    """Analyseur de profils de vitesse en temps reel"""
    
    def __init__(self, stage_controller):
        self.stage = stage_controller
        self.is_recording = False
        self.velocity_data = []
        self.time_data = []
        self.position_data = []
        self.start_time = None
        self.csv_file = None
        self.csv_writer = None
        
        # Plus besoin d'ajouter la méthode - elle est maintenant dans le wrapper
        print("Analyseur initialisé avec wrapper amélioré")
    
    def start_recording(self, axis="x"):
        """Demarre l'enregistrement des donnees de vitesse avec sauvegarde CSV"""
        self.is_recording = True
        self.velocity_data.clear()
        self.time_data.clear()
        self.position_data.clear()
        self.start_time = time.time()
        
        # Créer le fichier CSV avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"velocity_data_{axis}_{timestamp}.csv"
        
        # Ouvrir le fichier CSV pour écriture
        self.csv_file = open(csv_filename, 'w', newline='', encoding='utf-8')
        self.csv_writer = csv.writer(self.csv_file)
        
        # Écrire l'en-tête
        self.csv_writer.writerow(['Temps_s', 'Position_steps', 'Vitesse_steps_s'])
        self.csv_file.flush()  # Forcer l'écriture immédiate
        
        print(f"Demarrage de l'enregistrement des donnees de vitesse...")
        print(f"Sauvegarde CSV: {csv_filename}")
        
    def stop_recording(self):
        """Arrete l'enregistrement et ferme le fichier CSV"""
        self.is_recording = False
        
        # Fermer le fichier CSV
        if self.csv_file:
            self.csv_file.close()
            self.csv_file = None
            self.csv_writer = None
            
        print(f"Arret de l'enregistrement. {len(self.velocity_data)} points collectes.")
        
    def record_axis_data(self, axis, sampling_rate=20):
        """
        Enregistre les donnees de vitesse et position pour un axe avec sauvegarde CSV
        :param axis: Axe a surveiller ('x' ou 'y')
        :param sampling_rate: Frequence d'echantillonnage en Hz
        """
        sampling_interval = 1.0 / sampling_rate
        
        while self.is_recording:
            try:
                current_time = time.time() - self.start_time
                velocity = self.stage.get_current_axis_speed(axis)
                position = self.stage.get_position(axis)
                
                # Ajouter aux listes en mémoire
                self.time_data.append(current_time)
                self.velocity_data.append(velocity)
                self.position_data.append(position)
                
                # Écrire dans le fichier CSV immédiatement
                if self.csv_writer:
                    self.csv_writer.writerow([current_time, position, velocity])
                    self.csv_file.flush()  # Forcer l'écriture immédiate
                
                time.sleep(sampling_interval)
                
            except Exception as e:
                print(f"Erreur d'acquisition: {e}")
                # Même en cas d'erreur, écrire une ligne avec des valeurs par défaut
                if self.csv_writer:
                    current_time = time.time() - self.start_time if self.start_time else 0
                    self.csv_writer.writerow([current_time, "ERROR", "ERROR"])
                    self.csv_file.flush()
                time.sleep(sampling_interval)
                
    def execute_movement_test(self, axis, target_position, description=""):
        """
        Execute un test de mouvement avec enregistrement
        :param axis: Axe a tester
        :param target_position: Position cible
        :param description: Description du test
        """
        print(f"\nTest de mouvement {description}")
        print(f"Axe: {axis.upper()}, Position cible: {target_position}")
        
        # Verifier que l'axe est pret avant de bouger
        if not self.wait_for_axis_ready(axis):
            print(f"Erreur: axe {axis.upper()} non pret, abandon du test")
            return None
        
        # Demarrer l'enregistrement
        self.start_recording()
        
        # Lancer l'acquisition de donnees en parallele
        recording_thread = threading.Thread(
            target=self.record_axis_data, 
            args=(axis, 50),  # 50 Hz d'echantillonnage
            daemon=True
        )
        recording_thread.start()
        
        # Petite pause pour s'assurer que l'enregistrement a commence
        time.sleep(0.1)
        
        # Executer le mouvement
        print(f"Lancement du mouvement vers {target_position}...")
        movement_start = time.time()
        
        try:
            self.stage.move_to(axis, target_position)
            
            # SOLUTION: Arrêter l'enregistrement AVANT wait_move pour éviter les interférences
            print("Arret de l'enregistrement pendant l'attente...")
            self.stop_recording()
            
            # Attendre la fin du mouvement avec wait_move (plus fiable)
            print("Attente de la fin du mouvement...")
            self.stage.wait_move(axis, timeout=15)  # Timeout reduit pour mouvement normal
            
        except Exception as e:
            print(f"Erreur pendant le mouvement: {e}")
            # Arreter l'enregistrement en cas d'erreur
            self.stop_recording()
            return None
        
        movement_end = time.time()
        movement_duration = movement_end - movement_start
        
        print(f"Mouvement termine en {movement_duration:.2f}s")
        print(f"Position finale: {self.stage.get_position(axis)}")
        
        return {
            'axis': axis,
            'target': target_position,
            'duration': movement_duration,
            'time_data': self.time_data.copy(),
            'velocity_data': self.velocity_data.copy(),
            'position_data': self.position_data.copy(),
            'description': description
        }

    def execute_movement_test_with_recording(self, axis, target_position, description=""):
        """
        Version alternative qui enregistre plus de données mais compatible avec wait_move
        :param axis: Axe a tester
        :param target_position: Position cible
        :param description: Description du test
        """
        print(f"\nTest de mouvement avec enregistrement complet {description}")
        print(f"Axe: {axis.upper()}, Position cible: {target_position}")
        
        # Verifier que l'axe est pret avant de bouger
        if not self.wait_for_axis_ready(axis):
            print(f"Erreur: axe {axis.upper()} non pret, abandon du test")
            return None
        
        # Demarrer l'enregistrement
        self.start_recording()
        
        # Lancer l'acquisition de donnees en parallele
        recording_thread = threading.Thread(
            target=self.record_axis_data, 
            args=(axis, 30),  # Reduit a 30 Hz pour moins d'interference
            daemon=True
        )
        recording_thread.start()
        
        # Petite pause pour s'assurer que l'enregistrement a commence
        time.sleep(0.1)
        
        # Executer le mouvement
        print(f"Lancement du mouvement vers {target_position}...")
        movement_start = time.time()
        
        try:
            self.stage.move_to(axis, target_position)
            
            # Enregistrer pendant quelques secondes pour capturer l'acceleration
            time.sleep(2.0)
            
            # Arrêter l'enregistrement pour eviter les interferences avec wait_move
            print("Arret temporaire de l'enregistrement pour wait_move...")
            self.stop_recording()
            
            # Attendre la fin du mouvement
            print("Attente de la fin du mouvement...")
            self.stage.wait_move(axis, timeout=15)
            
            # Redemarrer brievement l'enregistrement pour capturer la fin
            print("Enregistrement final...")
            self.start_recording()
            final_thread = threading.Thread(
                target=self.record_axis_data, 
                args=(axis, 20),
                daemon=True
            )
            final_thread.start()
            time.sleep(0.5)  # Enregistrer la fin
            self.stop_recording()
            
        except Exception as e:
            print(f"Erreur pendant le mouvement: {e}")
            self.stop_recording()
            return None
        
        movement_end = time.time()
        movement_duration = movement_end - movement_start
        
        print(f"Mouvement termine en {movement_duration:.2f}s")
        print(f"Position finale: {self.stage.get_position(axis)}")
        
        return {
            'axis': axis,
            'target': target_position,
            'duration': movement_duration,
            'time_data': self.time_data.copy(),
            'velocity_data': self.velocity_data.copy(),
            'position_data': self.position_data.copy(),
            'description': description
        }

    def wait_for_axis_ready(self, axis, max_wait=10):
        """
        Attend que l'axe soit pret pour un nouveau mouvement
        :param axis: Axe a verifier
        :param max_wait: Temps d'attente maximum en secondes
        """
        print(f"Verification de l'etat de l'axe {axis.upper()}...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                # Utiliser is_moving() qui est plus fiable et moins intrusif
                is_moving = self.stage.stage.is_moving()
                axis_index = 0 if axis.lower() == 'x' else 1  # x=0, y=1
                
                if not is_moving[axis_index]:
                    print(f"Axe {axis.upper()} pret")
                    return True
                    
                print(f"Axe {axis.upper()} en mouvement, attente...")
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Erreur lors de la verification: {e}")
                time.sleep(0.5)
        
        print(f"Timeout: axe {axis.upper()} non pret apres {max_wait}s")
        return False

def plot_velocity_profiles(test_results):
    """Trace les profils de vitesse pour tous les tests"""
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle('Profils de Vitesse et Position - Tests de Validation', fontsize=16)
    
    colors = ['blue', 'red', 'green', 'orange']
    
    for i, result in enumerate(test_results):
        color = colors[i % len(colors)]
        
        # Graphique vitesse
        ax1.plot(result['time_data'], result['velocity_data'], 
                color=color, label=f"{result['description']}", linewidth=2)
        
        # Graphique position
        ax2.plot(result['time_data'], result['position_data'], 
                color=color, label=f"{result['description']}", linewidth=2)
    
    # Configuration des graphiques
    ax1.set_title('Profils de Vitesse')
    ax1.set_xlabel('Temps (s)')
    ax1.set_ylabel('Vitesse (steps/s)')
    ax1.legend()
    ax1.grid(True)
    
    ax2.set_title('Profils de Position')
    ax2.set_xlabel('Temps (s)')
    ax2.set_ylabel('Position (steps)')
    ax2.legend()
    ax2.grid(True)
    
    plt.tight_layout()
    
    # Sauvegarder le graphique
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"velocity_profiles_{timestamp}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Graphiques sauvegardes: {filename}")
    
    plt.show()

def main():
    """Script principal simplifié - Test vitesse sans wait_move"""
    
    print("=== TEST SIMPLIFIE DE PROFIL DE VITESSE ===")
    print("Initialisation du controleur Arcus Performax...")
    stage = EFImagingStageController(DLL_PATH)
    analyzer = VelocityProfileAnalyzer(stage)
    
    try:
        # Phase 1: Homing X uniquement
        print("\n" + "="*50)
        print("PHASE 1: HOMING AXE X")
        print("="*50)
        
        print("Homing de l'axe X...")
        stage.home('x')  # La méthode home() attend maintenant correctement
        
        print(f"Homing X termine - Position finale: {stage.get_position('x')}")
        
        # Pause de sécurité
        print("Pause de securite de 2 secondes...")
        time.sleep(2)
        
        # Phase 2: Test de mouvement simple
        print("\n" + "="*50)
        print("PHASE 2: TEST DE MOUVEMENT AVEC ACQUISITION")
        print("="*50)
        
        # Position cible
        target_position = 4000
        print(f"Mouvement X vers position {target_position}")
        
        # Démarrer l'enregistrement
        print("Demarrage de l'enregistrement...")
        analyzer.start_recording('x')  # Passer l'axe pour le nom du fichier
        
        # Lancer le thread d'acquisition
        recording_thread = threading.Thread(
            target=analyzer.record_axis_data, 
            args=('x', 20),  # 20 Hz d'echantillonnage
            daemon=True
        )
        recording_thread.start()
        
        # Petite pause pour s'assurer que l'enregistrement a commence
        time.sleep(0.5)
        
        # Vérifier que l'enregistrement fonctionne
        if len(analyzer.velocity_data) == 0:
            print("ATTENTION: L'enregistrement ne semble pas fonctionner!")
        else:
            print(f"Enregistrement OK - {len(analyzer.velocity_data)} points deja collectes")
        
        # Lancer le mouvement
        print(f"Lancement du mouvement vers {target_position}...")
        movement_start = time.time()
        stage.move_to('x', target_position)
        
        # Enregistrer pendant 10 secondes (pas de wait_move)
        print("Enregistrement pendant 10 secondes...")
        try:
            for i in range(10):
                time.sleep(1)
                
                # Vérifier si le thread d'acquisition est encore vivant
                if not recording_thread.is_alive():
                    print(f"ATTENTION: Thread d'acquisition arrêté à {i+1}s")
                    break
                    
        except KeyboardInterrupt:
            print("Interruption utilisateur - arrêt de l'acquisition...")
        except Exception as e:
            print(f"Erreur pendant l'acquisition: {e}")
        finally:
            analyzer.stop_recording()
        
        movement_end = time.time()
        
        print(f"Enregistrement termine apres {movement_end - movement_start:.1f}s")
        print(f"Position finale X: {stage.get_position('x')}")
        print(f"Nombre total de points collectes: {len(analyzer.velocity_data)}")
        print(f"Fichier CSV sauvegarde avec {len(analyzer.velocity_data)} lignes de donnees")
        
        # Phase 3: Tracer le graphique
        print("\n" + "="*50)
        print("PHASE 3: VISUALISATION")
        print("="*50)
        
        # Vérifier qu'on a des données à tracer
        if len(analyzer.velocity_data) == 0 or len(analyzer.time_data) == 0:
            print("ERREUR: Aucune donnee collectee, impossible de tracer les graphiques!")
            return
            
        print(f"Donnees collectees: {len(analyzer.velocity_data)} points sur {analyzer.time_data[-1]:.2f}s")
        
        # Créer le graphique simple
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        fig.suptitle('Profil de Vitesse - Test Simplifié Axe X', fontsize=16)
        
        # Graphique vitesse
        ax1.plot(analyzer.time_data, analyzer.velocity_data, 'b-', linewidth=2, label='Vitesse X')
        ax1.set_title('Profil de Vitesse')
        ax1.set_xlabel('Temps (s)')
        ax1.set_ylabel('Vitesse (steps/s)')
        ax1.legend()
        ax1.grid(True)
        
        # Graphique position
        ax2.plot(analyzer.time_data, analyzer.position_data, 'r-', linewidth=2, label='Position X')
        ax2.set_title('Profil de Position')
        ax2.set_xlabel('Temps (s)')
        ax2.set_ylabel('Position (steps)')
        ax2.legend()
        ax2.grid(True)
        
        plt.tight_layout()
        
        # Sauvegarder le graphique
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"velocity_profile_simple_{timestamp}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Graphique sauvegarde: {filename}")
        
        # Afficher les statistiques
        print(f"\nStatistiques:")
        print(f"  Duree d'enregistrement: {analyzer.time_data[-1]:.2f}s")
        print(f"  Nombre de points: {len(analyzer.velocity_data)}")
        if len(analyzer.velocity_data) > 0:
            print(f"  Vitesse maximale: {max(analyzer.velocity_data)} steps/s")
            print(f"  Position finale: {analyzer.position_data[-1]} steps")
        
        plt.show()
        
        print("\nTest simplifie termine avec succes!")
        
    except Exception as e:
        print(f"Erreur pendant le test: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Fermer la connexion
        try:
            analyzer.stop_recording()  # S'assurer que l'enregistrement est arrêté et CSV fermé
        except:
            pass
        stage.close()
        print("Connexion fermee.")

if __name__ == "__main__":
    main() 