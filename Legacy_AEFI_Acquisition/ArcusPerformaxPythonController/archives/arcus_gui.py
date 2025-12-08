# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
import sys
import os

# Ajout du chemin parent au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ArcusPerformaxPythonController.controller.EFImagingBench_Controller_ArcusPerformax4EXStage import ArcusController

# Paramètres
DLL_PATH = r"C:/Users/manip/Dropbox/Luis/1 PROJETS/1 - THESE/Ressources/ExperimentalData_ASSOCE/Dev/ArcusPerformaxPythonController/DLL64"

class ArcusGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Arcus Performax XY - Contrôle")
        self.geometry("580x350")
        self.configure(bg="#d0d0d0")
        
        # Initialisation du contrôleur (qui applique déjà les paramètres par défaut)
        self.controller = ArcusController(DLL_PATH)
        
        # Construction de l'interface
        self._build_widgets()
        
        # Récupération et affichage des paramètres actuels
        self._update_speed_displays()
        
    def _update_speed_displays(self):
        """Met à jour l'affichage des paramètres de vitesse depuis le contrôleur"""
        # Mise à jour des champs de saisie pour chaque axe
        for axis in ["x", "y"]:
            params = self.controller.get_axis_params(axis)
            self.axis_vars[axis]["ls"].set(str(params["ls"]))
            self.axis_vars[axis]["hs"].set(str(params["hs"]))
            self.axis_vars[axis]["acc"].set(str(params["acc"]))
        
        self.log_var.set("Affichage des paramètres actuels")
        
    def _build_widgets(self):
        # Conteneur principal avec marge
        main_frame = tk.Frame(self, bg="#d0d0d0")
        main_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        # ======== Section des axes (X et Y) ========
        axes_frame = tk.Frame(main_frame, bg="#d5d5d5", bd=2, relief="raised")
        axes_frame.pack(fill="x", padx=0, pady=5)
        
        # En-têtes pour la section des axes
        headers = ["axis", "enabled\nstate", '"Jog To"\nvalue', "Jog To", "Home", "Stop\nSlow", "Stop\nNow!"]
        header_frame = tk.Frame(axes_frame, bg="#d5d5d5")
        header_frame.pack(fill="x", padx=5, pady=(5, 0))
        
        # Configuration des colonnes pour un meilleur alignement
        col_widths = [60, 80, 90, 80, 80, 80, 80]
        
        for i, header in enumerate(headers):
            lbl = tk.Label(header_frame, text=header, font=("Arial", 8, "bold"), bg="#d5d5d5", width=len(header)+2)
            lbl.grid(row=0, column=i, padx=0)
            
        # Variables et widgets pour chaque axe
        self.axis_vars = {}
        
        for idx, axis_label in enumerate([("X", "00"), ("Y", "(Y)")]):
            axis, label = axis_label
            axis_lower = axis.lower()
            
            # Cadre pour chaque ligne d'axe avec couleur de fond distincte
            row_bg = "#c0c0c0" if idx % 2 == 0 else "#c5c5c5"
            row_frame = tk.Frame(axes_frame, bg=row_bg, height=50)
            row_frame.pack(fill="x", padx=0, pady=0)
            row_frame.pack_propagate(False)  # Maintient une hauteur fixe
            
            # Étiquette de l'axe
            axis_label = tk.Label(row_frame, text=label, width=4, bg=row_bg, font=("Arial", 9))
            axis_label.place(x=col_widths[0]//2, y=25, anchor="center")
            
            # Interrupteur ON/OFF
            enabled_frame = tk.Frame(row_frame, bg="#808080", width=60, height=40, bd=1, relief="raised")
            enabled_frame.place(x=col_widths[0] + col_widths[1]//2, y=25, anchor="center")
            
            enabled_var = tk.BooleanVar(value=True)
            enabled_label = tk.Label(enabled_frame, text="ON", bg="#808080", fg="white", font=("Arial", 9, "bold"))
            enabled_label.place(relx=0.5, rely=0.3, anchor="center")
            
            checkbox = tk.Checkbutton(enabled_frame, variable=enabled_var, bg="#808080", 
                                    command=lambda a=axis_lower, v=enabled_var: self.toggle_axis(a, v))
            checkbox.place(relx=0.5, rely=0.7, anchor="center")
            
            # Entrée position cible
            jog_var = tk.StringVar(value="14950")
            jog_entry = tk.Entry(row_frame, textvariable=jog_var, width=8, justify="center", 
                              bg="white", font=("Arial", 9))
            jog_entry.place(x=col_widths[0] + col_widths[1] + col_widths[2]//2, y=25, anchor="center")
            
            # Bouton JOG TO
            jog_btn = tk.Button(row_frame, text="JOG TO", bg="#d0d0d0", font=("Arial", 8, "bold"),
                             command=lambda a=axis_lower: self.jog_axis(a), width=7)
            jog_btn.place(x=col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3]//2, y=25, anchor="center")
            
            # Bouton HOME
            home_btn = tk.Button(row_frame, text="HOME", bg="#d0d0d0", font=("Arial", 8, "bold"),
                              command=lambda a=axis_lower: self.home_axis(a), width=7)
            home_btn.place(x=col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3] + col_widths[4]//2, y=25, anchor="center")
            
            # Bouton STOP SLOW (carré rouge)
            stop_slow_btn = tk.Button(row_frame, bg="red", width=5, height=1, relief="raised",
                                   command=lambda a=axis_lower: self.stop_axis(a, False))
            stop_slow_btn.place(x=col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3] + col_widths[4] + col_widths[5]//2, y=25, anchor="center")
            
            # Bouton STOP NOW (X rouge)
            stop_now_btn = tk.Button(row_frame, bg="red", text="X", fg="white", font=("Arial", 9, "bold"), 
                                  width=5, height=1, relief="raised",
                                  command=lambda a=axis_lower: self.stop_axis(a, True))
            stop_now_btn.place(x=col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3] + col_widths[4] + col_widths[5] + col_widths[6]//2, y=25, anchor="center")
            
            # Position actuelle (invisible mais stockée)
            pos_var = tk.StringVar(value="0")
            
            # Stockage des variables
            self.axis_vars[axis_lower] = {
                "enabled": enabled_var, 
                "pos": pos_var,
                "jog": jog_var,
                "ls": tk.StringVar(value="10"),  # Valeurs par défaut, seront mises à jour
                "hs": tk.StringVar(value="800"),
                "acc": tk.StringVar(value="300")
            }
        
        # ======== Section des vitesses/accélérations ========
        speed_frame = tk.Frame(main_frame, bg="#d5d5d5", bd=2, relief="raised")
        speed_frame.pack(fill="x", padx=0, pady=10)
        
        # Étiquettes
        headers_frame = tk.Frame(speed_frame, bg="#d5d5d5")
        headers_frame.pack(fill="x", padx=5, pady=5)
        
        tk.Label(headers_frame, text="Low speed", bg="#d5d5d5", font=("Arial", 8, "bold")).grid(row=0, column=1, padx=25)
        tk.Label(headers_frame, text="High speed", bg="#d5d5d5", font=("Arial", 8, "bold")).grid(row=0, column=2, padx=25)
        tk.Label(headers_frame, text="Acceleration", bg="#d5d5d5", font=("Arial", 8, "bold")).grid(row=0, column=3, padx=25)
        
        # Conteneur pour les champs de vitesse/accélération
        values_frame = tk.Frame(speed_frame, bg="#d5d5d5")
        values_frame.pack(fill="x", padx=5, pady=5)
        
        # Champs pour X et Y
        for idx, axis in enumerate(["x", "y"]):
            row_bg = "#d5d5d5"
            # Étiquette de l'axe
            tk.Label(values_frame, text=axis.upper(), bg=row_bg, font=("Arial", 9, "bold"), width=4).grid(row=idx, column=0, padx=10, pady=10)
            
            # Low speed
            ls_entry = tk.Entry(values_frame, textvariable=self.axis_vars[axis]["ls"], width=8, justify="center", bg="white")
            ls_entry.grid(row=idx, column=1, padx=25, pady=5)
            
            # High speed
            hs_entry = tk.Entry(values_frame, textvariable=self.axis_vars[axis]["hs"], width=8, justify="center", bg="white") 
            hs_entry.grid(row=idx, column=2, padx=25, pady=5)
            
            # Acceleration
            acc_entry = tk.Entry(values_frame, textvariable=self.axis_vars[axis]["acc"], width=8, justify="center", bg="white") 
            acc_entry.grid(row=idx, column=3, padx=25, pady=5)
        
        # Bouton SET ACC & SPEEDS
        set_speeds_btn = tk.Button(values_frame, text="SET\nACC &\nSPEEDS", 
                                 bg="#d0d0d0", font=("Arial", 8, "bold"),
                                 command=self.apply_speeds, height=3, width=8, relief="raised")
        set_speeds_btn.grid(row=0, column=4, rowspan=2, padx=10, pady=5)
        
        # ======== Zone de log/status ========
        self.log_var = tk.StringVar()
        log_frame = tk.Frame(main_frame, bg="#d5d5d5", bd=1, relief="sunken", height=30)
        log_frame.pack(fill="x", padx=0, pady=5)
        log_frame.pack_propagate(False)  # Maintient une hauteur fixe
        
        log_label = tk.Label(log_frame, textvariable=self.log_var, font=("Arial", 9), 
                          bg="#d5d5d5", anchor="w", padx=10)
        log_label.pack(fill="both", expand=True)
        
        # Rafraîchissement périodique
        self.after(500, self.refresh_positions)
    
    def toggle_axis(self, axis, var):
        """Active/désactive un axe"""
        x_on = self.axis_vars["x"]["enabled"].get()
        y_on = self.axis_vars["y"]["enabled"].get()
        self.controller.enable(x_on, y_on)
        self.log_var.set(f"Axes activés : X={x_on}, Y={y_on}")
    
    def jog_axis(self, axis):
        """Déplace un axe à une position absolue"""
        try:
            pos = float(self.axis_vars[axis]["jog"].get())
            self.controller.jog_to(axis, pos)
            self.log_var.set(f"Déplacement axe {axis.upper()} → {pos}")
        except Exception as e:
            self.log_var.set(f"Erreur jog {axis}: {e}")
    
    def home_axis(self, axis):
        """Lance le homing d'un axe"""
        try:
            self.controller.home(axis)
            self.log_var.set(f"Homing axe {axis.upper()} lancé")
        except Exception as e:
            self.log_var.set(f"Erreur home {axis}: {e}")
    
    def stop_axis(self, axis, immediate=False):
        """Arrête le mouvement d'un axe"""
        try:
            self.controller.stop(axis, immediate=immediate)
            if immediate:
                msg = f"Arrêt IMMÉDIAT axe {axis.upper()}"
            else:
                msg = f"Arrêt contrôlé axe {axis.upper()}"
            self.log_var.set(msg)
        except Exception as e:
            self.log_var.set(f"Erreur stop {axis}: {e}")
    
    def apply_speeds(self):
        """Applique les paramètres de vitesse pour chaque axe"""
        try:
            # Appliquer les paramètres pour chaque axe
            for axis in ["x", "y"]:
                ls = int(self.axis_vars[axis]["ls"].get())
                hs = int(self.axis_vars[axis]["hs"].get())
                acc = int(self.axis_vars[axis]["acc"].get())
                
                # Appliquer les paramètres via le contrôleur
                self.controller.set_axis_params(axis, ls=ls, hs=hs, acc=acc)
            
            self.log_var.set("Paramètres de vitesse appliqués pour chaque axe")
        except Exception as e:
            self.log_var.set(f"Erreur paramètres: {e}")
    
    def refresh_positions(self):
        """Met à jour l'affichage des positions en temps réel"""
        try:
            for axis in ["x", "y"]:
                pos = self.controller.get_position(axis)
                self.axis_vars[axis]["pos"].set(f"{pos:.2f}")
                
                # Récupérer aussi périodiquement le statut des axes
                # status = self.controller.get_status(axis)
                # Si nécessaire, ajouter du code pour afficher le statut
        except Exception:
            pass
        self.after(500, self.refresh_positions)
    
    def on_closing(self):
        """Ferme proprement le contrôleur lors de la fermeture de l'application"""
        self.controller.close()
        self.destroy()

if __name__ == "__main__":
    app = ArcusGUI()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop() 