#!/usr/bin/env python3
"""
Script pour extraire le texte du fichier PDF LSM9DS1
et le convertir en fichier texte lisible
"""

import os
import sys

def extract_with_pypdf2():
    """Méthode 1: Utilisation de PyPDF2"""
    try:
        import PyPDF2
        
        pdf_path = "lsm9ds1.pdf"
        txt_path = "lsm9ds1_extracted_pypdf2.txt"
        
        print("🔍 Extraction avec PyPDF2...")
        
        with open(pdf_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            print(f"📄 Nombre de pages: {len(pdf_reader.pages)}")
            
            text_content = []
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    text = page.extract_text()
                    if text.strip():
                        text_content.append(f"\n=== PAGE {page_num + 1} ===\n")
                        text_content.append(text)
                        text_content.append("\n" + "="*50 + "\n")
                except Exception as e:
                    print(f"❌ Erreur page {page_num + 1}: {e}")
                    continue
            
            # Sauvegarder le texte extrait
            with open(txt_path, 'w', encoding='utf-8') as txt_file:
                txt_file.write("".join(text_content))
            
            print(f"✅ Texte extrait sauvegardé: {txt_path}")
            return txt_path
            
    except ImportError:
        print("❌ PyPDF2 non disponible")
        return None
    except Exception as e:
        print(f"❌ Erreur avec PyPDF2: {e}")
        return None

def extract_with_pdfplumber():
    """Méthode 2: Utilisation de pdfplumber (plus précis)"""
    try:
        import pdfplumber
        
        pdf_path = "lsm9ds1.pdf"
        txt_path = "lsm9ds1_extracted_pdfplumber.txt"
        
        print("🔍 Extraction avec pdfplumber...")
        
        text_content = []
        
        with pdfplumber.open(pdf_path) as pdf:
            print(f"📄 Nombre de pages: {len(pdf.pages)}")
            
            for page_num, page in enumerate(pdf.pages):
                try:
                    text = page.extract_text()
                    if text and text.strip():
                        text_content.append(f"\n=== PAGE {page_num + 1} ===\n")
                        text_content.append(text)
                        text_content.append("\n" + "="*50 + "\n")
                        
                        # Extraire aussi les tableaux si présents
                        tables = page.extract_tables()
                        if tables:
                            text_content.append(f"\n--- TABLEAUX PAGE {page_num + 1} ---\n")
                            for table_num, table in enumerate(tables):
                                text_content.append(f"\nTableau {table_num + 1}:\n")
                                for row in table:
                                    if row:
                                        text_content.append(" | ".join([cell or "" for cell in row]) + "\n")
                            text_content.append("\n")
                            
                except Exception as e:
                    print(f"❌ Erreur page {page_num + 1}: {e}")
                    continue
        
        # Sauvegarder le texte extrait
        with open(txt_path, 'w', encoding='utf-8') as txt_file:
            txt_file.write("".join(text_content))
        
        print(f"✅ Texte extrait sauvegardé: {txt_path}")
        return txt_path
        
    except ImportError:
        print("❌ pdfplumber non disponible")
        return None
    except Exception as e:
        print(f"❌ Erreur avec pdfplumber: {e}")
        return None

def extract_with_pymupdf():
    """Méthode 3: Utilisation de PyMuPDF (fitz)"""
    try:
        import fitz  # PyMuPDF
        
        pdf_path = "lsm9ds1.pdf"
        txt_path = "lsm9ds1_extracted_pymupdf.txt"
        
        print("🔍 Extraction avec PyMuPDF...")
        
        doc = fitz.open(pdf_path)
        print(f"📄 Nombre de pages: {doc.page_count}")
        
        text_content = []
        
        for page_num in range(doc.page_count):
            try:
                page = doc[page_num]
                text = page.get_text()
                
                if text.strip():
                    text_content.append(f"\n=== PAGE {page_num + 1} ===\n")
                    text_content.append(text)
                    text_content.append("\n" + "="*50 + "\n")
                    
            except Exception as e:
                print(f"❌ Erreur page {page_num + 1}: {e}")
                continue
        
        doc.close()
        
        # Sauvegarder le texte extrait
        with open(txt_path, 'w', encoding='utf-8') as txt_file:
            txt_file.write("".join(text_content))
        
        print(f"✅ Texte extrait sauvegardé: {txt_path}")
        return txt_path
        
    except ImportError:
        print("❌ PyMuPDF non disponible")
        return None
    except Exception as e:
        print(f"❌ Erreur avec PyMuPDF: {e}")
        return None

def search_odr_frequencies(txt_file):
    """Recherche les informations sur les fréquences ODR dans le texte extrait"""
    try:
        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("\n🔍 Recherche des fréquences ODR...")
        
        # Mots-clés à rechercher
        keywords = [
            'ODR', 'output data rate', 'sampling rate', 'frequency', 'Hz',
            'magnetometer', 'accelerometer', 'gyroscope', 'mag', 'acc', 'gyr',
            'maximum', 'max', 'rate'
        ]
        
        # Rechercher les lignes contenant ces mots-clés
        lines = content.split('\n')
        relevant_lines = []
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(keyword.lower() in line_lower for keyword in keywords):
                # Inclure le contexte (lignes précédentes et suivantes)
                start = max(0, i-2)
                end = min(len(lines), i+3)
                context = lines[start:end]
                relevant_lines.extend([f"Ligne {i+1}:"] + context + ["---"])
        
        # Sauvegarder les résultats
        search_results_file = "lsm9ds1_odr_search_results.txt"
        with open(search_results_file, 'w', encoding='utf-8') as f:
            f.write("=== RECHERCHE FRÉQUENCES ODR - LSM9DS1 ===\n\n")
            f.write("\n".join(relevant_lines))
        
        print(f"✅ Résultats de recherche sauvegardés: {search_results_file}")
        
        return search_results_file
        
    except Exception as e:
        print(f"❌ Erreur lors de la recherche: {e}")
        return None

def install_requirements():
    """Installe les bibliothèques nécessaires"""
    import subprocess
    
    libraries = [
        "PyPDF2",
        "pdfplumber", 
        "PyMuPDF"
    ]
    
    print("📦 Installation des bibliothèques nécessaires...")
    
    for lib in libraries:
        try:
            print(f"Installation de {lib}...")
            if lib == "PyMuPDF":
                subprocess.check_call([sys.executable, "-m", "pip", "install", "PyMuPDF"])
            else:
                subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
            print(f"✅ {lib} installé")
        except subprocess.CalledProcessError:
            print(f"❌ Échec installation {lib}")

def main():
    """Fonction principale"""
    print("🎛️ === EXTRACTEUR PDF LSM9DS1 ===\n")
    
    # Vérifier que le fichier PDF existe
    pdf_path = "lsm9ds1.pdf"
    if not os.path.exists(pdf_path):
        print(f"❌ Fichier PDF non trouvé: {pdf_path}")
        return
    
    print(f"📄 Fichier PDF trouvé: {pdf_path}")
    print(f"📏 Taille: {os.path.getsize(pdf_path) / 1024 / 1024:.2f} MB\n")
    
    # Demander si on veut installer les dépendances
    install_deps = input("Installer les dépendances automatiquement ? (y/n): ").lower().strip()
    if install_deps == 'y':
        install_requirements()
        print()
    
    # Essayer les différentes méthodes d'extraction
    extracted_files = []
    
    # Méthode 1: pdfplumber (recommandée)
    result = extract_with_pdfplumber()
    if result:
        extracted_files.append(result)
    
    # Méthode 2: PyMuPDF
    result = extract_with_pymupdf()
    if result:
        extracted_files.append(result)
    
    # Méthode 3: PyPDF2 (fallback)
    result = extract_with_pypdf2()
    if result:
        extracted_files.append(result)
    
    if not extracted_files:
        print("❌ Aucune méthode d'extraction n'a fonctionné")
        print("💡 Essayez d'installer les dépendances manuellement:")
        print("   pip install PyPDF2 pdfplumber PyMuPDF")
        return
    
    print(f"\n✅ {len(extracted_files)} fichier(s) texte créé(s)")
    
    # Rechercher les informations ODR dans le meilleur fichier
    best_file = extracted_files[0]  # Prendre le premier (pdfplumber si disponible)
    search_results = search_odr_frequencies(best_file)
    
    print("\n🎯 === RÉSUMÉ ===")
    print("Fichiers créés:")
    for file in extracted_files:
        print(f"  📄 {file}")
    
    if search_results:
        print(f"  🔍 {search_results}")
    
    print(f"\n💡 Vous pouvez maintenant lire le fichier texte pour trouver les spécifications ODR du LSM9DS1")

if __name__ == "__main__":
    main() 