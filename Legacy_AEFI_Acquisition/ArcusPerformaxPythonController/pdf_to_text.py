import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PyPDF2 import PdfReader

# Crée la fenêtre principale (cachée)
root = tk.Tk()
root.withdraw()

# Dossier de départ : répertoire du script
start_dir = os.path.dirname(os.path.abspath(__file__))

# Ouvre la boîte de dialogue pour sélectionner un PDF
file_path = filedialog.askopenfilename(
    title="Sélectionnez un fichier PDF à extraire",
    initialdir=start_dir,
    filetypes=[("Fichiers PDF", "*.pdf")]
)

if not file_path:
    print("Aucun fichier sélectionné.")
    exit()

# Extraction du texte
try:
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
except Exception as e:
    messagebox.showerror("Erreur", f"Erreur lors de l'extraction du texte :\n{e}")
    exit()

# Sauvegarde dans un fichier .txt
txt_path = os.path.splitext(file_path)[0] + ".txt"
try:
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)
    messagebox.showinfo("Succès", f"Extraction terminée :\n{txt_path}")
except Exception as e:
    messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde du fichier texte :\n{e}")
