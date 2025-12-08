# 2025-05-15 Luis Saluden

# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
from pylablib.devices import Arcus
import pylablib as pll

# Chemin vers les DLLs Arcus
pll.par["devices/dlls/arcus_performax"] = r"C:/Users/manip/Dropbox/Luis/1 PROJETS/1 - THESE/Ressources/ExperimentalData_ASSOCE/Dev/ArcusPerformaxPythonController/DLL64"
stage = Arcus.Performax4EXStage()

# Style moderne
root = tk.Tk()
root.title("Arcus Performax - Contrôle XY")
root.configure(bg="#f7f6f2")
style = ttk.Style()
style.theme_use('clam')
style.configure("TButton", padding=6, font=("Segoe UI", 11))
style.configure("TCheckbutton", font=("Segoe UI", 11))
style.configure("TLabel", font=("Segoe UI", 11))

log = tk.StringVar()
log.set("Prêt.")

# Variables
enable_x_var = tk.IntVar(value=1)
enable_y_var = tk.IntVar(value=1)
jog_x = tk.StringVar(value="0")
jog_y = tk.StringVar(value="0")
lspeed_x = tk.StringVar(value="10")
hspeed_x = tk.StringVar(value="800")
acc_x = tk.StringVar(value="300")
lspeed_y = tk.StringVar(value="10")
hspeed_y = tk.StringVar(value="800")
acc_y = tk.StringVar(value="300")

# Fonctions de contrôle
def set_acc_speeds():
    try:
        stage.query(f"LS1={int(lspeed_x.get())}")
        stage.query(f"HS1={int(hspeed_x.get())}")
        stage.query(f"ACC1={int(acc_x.get())}")
        stage.query(f"DEC1={int(acc_x.get())}")
        stage.query(f"LS2={int(lspeed_y.get())}")
        stage.query(f"HS2={int(hspeed_y.get())}")
        stage.query(f"ACC2={int(acc_y.get())}")
        stage.query(f"DEC2={int(acc_y.get())}")
        log.set("Vitesses et accélérations mises à jour.")
    except Exception as e:
        log.set(f"Erreur : {e}")

def jog_to(axis):
    try:
        pos = int(jog_x.get()) if axis == "x" else int(jog_y.get())
        stage.move_to(axis, pos)
        log.set(f"Jog {axis.upper()} vers {pos}")
    except Exception as e:
        log.set(f"Erreur : {e}")

def home(axis):
    try:
        stage.home(axis, direction="-", home_mode="only_home_input")
        log.set(f"Homing {axis.upper()} terminé.")
    except Exception as e:
        log.set(f"Erreur : {e}")

def stop(axis, immediate=False):
    try:
        stage.stop(axis, immediate=immediate)
        log.set(f"Stop {axis.upper()} {'immédiat' if immediate else 'lent'}")
    except Exception as e:
        log.set(f"Erreur : {e}")

def toggle_enable(axis):
    try:
        val = enable_x_var.get() if axis == "x" else enable_y_var.get()
        eo_val = 1 if enable_x_var.get() else 0
        eo_val += 2 if enable_y_var.get() else 0
        stage.query(f"EO={eo_val}")
        log.set(f"Axe {axis.upper()} {'activé' if val else 'désactivé'}")
    except Exception as e:
        log.set(f"Erreur : {e}")

# En-tête
headers = ["axis", "enabled state", '"Jog To" value', "Jog To", "Home", "Stop Slow", "Stop Now!"]
for col, text in enumerate(headers):
    ttk.Label(root, text=text).grid(row=0, column=col, padx=8, pady=6)

# Ligne X
ttk.Label(root, text="(X)").grid(row=1, column=0, padx=8, pady=6)
ttk.Checkbutton(root, variable=enable_x_var, command=lambda: toggle_enable("x")).grid(row=1, column=1)
ttk.Entry(root, textvariable=jog_x, width=8).grid(row=1, column=2)
ttk.Button(root, text="JOG TO", command=lambda: jog_to("x")).grid(row=1, column=3)
ttk.Button(root, text="HOME", command=lambda: home("x")).grid(row=1, column=4)
ttk.Button(root, text="■", command=lambda: stop("x", False), style="TButton", width=2).grid(row=1, column=5)
ttk.Button(root, text="■", command=lambda: stop("x", True), style="TButton", width=2).grid(row=1, column=6)

# Ligne Y
ttk.Label(root, text="(Y)").grid(row=2, column=0, padx=8, pady=6)
ttk.Checkbutton(root, variable=enable_y_var, command=lambda: toggle_enable("y")).grid(row=2, column=1)
ttk.Entry(root, textvariable=jog_y, width=8).grid(row=2, column=2)
ttk.Button(root, text="JOG TO", command=lambda: jog_to("y")).grid(row=2, column=3)
ttk.Button(root, text="HOME", command=lambda: home("y")).grid(row=2, column=4)
ttk.Button(root, text="■", command=lambda: stop("y", False), style="TButton", width=2).grid(row=2, column=5)
ttk.Button(root, text="■", command=lambda: stop("y", True), style="TButton", width=2).grid(row=2, column=6)

# Ligne paramètres X/Y
ttk.Label(root, text="X").grid(row=3, column=0, padx=8, pady=6)
ttk.Entry(root, textvariable=lspeed_x, width=8).grid(row=3, column=1)
ttk.Entry(root, textvariable=hspeed_x, width=8).grid(row=3, column=2)
ttk.Entry(root, textvariable=acc_x, width=8).grid(row=3, column=3)

ttk.Label(root, text="Y").grid(row=4, column=0, padx=8, pady=6)
ttk.Entry(root, textvariable=lspeed_y, width=8).grid(row=4, column=1)
ttk.Entry(root, textvariable=hspeed_y, width=8).grid(row=4, column=2)
ttk.Entry(root, textvariable=acc_y, width=8).grid(row=4, column=3)

# Bouton SET ACC & SPEEDS
ttk.Button(root, text="SET ACC & SPEEDS", command=set_acc_speeds).grid(row=3, column=4, rowspan=2, columnspan=3, padx=8, pady=6, sticky="nsew")

# Log
ttk.Label(root, textvariable=log, foreground="#2a4d69", font=("Segoe UI", 13, "bold")).grid(row=5, column=0, columnspan=7, pady=10)

def on_close():
    stage.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop() 