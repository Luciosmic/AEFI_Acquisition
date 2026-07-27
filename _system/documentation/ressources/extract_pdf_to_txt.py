#!/usr/bin/env python3
"""
Script pour extraire le texte de tous les fichiers PDF dans le dossier courant
et les sauvegarder en fichiers .txt
"""

import os
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        print("Erreur: pypdf ou PyPDF2 n'est pas installé.")
        print("Installez-le avec: pip install pypdf")
        exit(1)


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extrait le texte d'un fichier PDF.
    
    Parameters
    ----------
    pdf_path : Path
        Chemin vers le fichier PDF
        
    Returns
    -------
    str
        Texte extrait du PDF
    """
    text = []
    try:
        reader = PdfReader(str(pdf_path))
        num_pages = len(reader.pages)
        
        print(f"  Extraction de {num_pages} page(s)...")
        
        for page_num, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text()
                if page_text.strip():
                    text.append(page_text)
                print(f"    Page {page_num}/{num_pages} extraite")
            except Exception as e:
                print(f"    Erreur lors de l'extraction de la page {page_num}: {e}")
                continue
                
    except Exception as e:
        print(f"  Erreur lors de la lecture du PDF: {e}")
        return ""
    
    return "\n\n".join(text)


def process_pdfs_in_directory(directory: Path):
    """
    Traite tous les fichiers PDF dans un répertoire.
    
    Parameters
    ----------
    directory : Path
        Répertoire contenant les fichiers PDF
    """
    pdf_files = list(directory.glob("*.pdf"))
    
    if not pdf_files:
        print(f"Aucun fichier PDF trouvé dans {directory}")
        return
    
    print(f"Trouvé {len(pdf_files)} fichier(s) PDF à traiter\n")
    
    for pdf_path in pdf_files:
        print(f"Traitement de: {pdf_path.name}")
        
        # Créer le nom du fichier de sortie
        txt_path = pdf_path.with_suffix('.txt')
        
        # Extraire le texte
        text = extract_text_from_pdf(pdf_path)
        
        if text.strip():
            # Sauvegarder le texte
            try:
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                print(f"  ✓ Texte sauvegardé dans: {txt_path.name}\n")
            except Exception as e:
                print(f"  ✗ Erreur lors de la sauvegarde: {e}\n")
        else:
            print(f"  ⚠ Aucun texte extrait du PDF\n")


if __name__ == "__main__":
    # Obtenir le répertoire du script
    script_dir = Path(__file__).parent
    
    print("=" * 60)
    print("Extraction de texte depuis les fichiers PDF")
    print("=" * 60)
    print(f"Répertoire: {script_dir}\n")
    
    process_pdfs_in_directory(script_dir)
    
    print("=" * 60)
    print("Extraction terminée!")
    print("=" * 60)







