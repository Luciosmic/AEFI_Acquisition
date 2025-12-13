# AEFI Acquisition - Banc de Test Champ Électrique

## Configuration Environnement Python

### ⚠️ Prérequis Critique : Python 64-bit

**Problème identifié** : Les DLL Arcus Performax 4EX (dans `DLL64/`) sont en **64-bit**. Un Python 32-bit ne peut pas charger ces DLL, ce qui provoque l'erreur :
```
AttributeError: 'NoneType' object has no attribute 'argtypes'
```

**Solution** : Utiliser **obligatoirement** un environnement Python 64-bit.

### Vérification de l'architecture Python

```bash
python -c "import platform; print(platform.architecture())"
```

- ✅ Attendu : `('64bit', 'WindowsPE')`
- ❌ Problématique : `('32bit', 'WindowsPE')`

### Environnements Virtuels

#### venv64 (Recommandé - 64-bit)
```bash
# Depuis la racine du projet
.\venv64\Scripts\Activate.ps1
```

#### venv_windows_efi_imaging_bench (⚠️ 32-bit - Ne pas utiliser pour Arcus)
Cet environnement est en 32-bit et **ne peut pas** se connecter au matériel Arcus.

### Installation Python 64-bit

Si Python 64-bit n'est pas installé :
1. Télécharger Python 3.7+ 64-bit depuis https://www.python.org/downloads/
2. Installer (cocher "Add to PATH")
3. Créer un venv 64-bit :
   ```bash
   python -m venv venv64
   venv64\Scripts\activate
   pip install -r requirements.txt
   ```

### Test de Connexion Arcus

Pour vérifier la connexion au matériel Arcus :
```bash
.\venv64\Scripts\python.exe Legacy_AEFI_Acquisition\EFImagingBench_App\src\infrastructure\arcus_performax_4EX\test_driver_arcus_minimal.py
```

Sortie attendue :
```
✓ Connection successful!
Stage info: (0, '4ex00', 'Performax USB', ...)
```

## Structure du Projet

*(À compléter)*

## Dépendances Matérielles

- **Arcus Performax 4EX** : Contrôleur moteur (nécessite DLL 64-bit)
- **ADS131A04** : ADC pour acquisition tension
- **MCU** : Microcontrôleur (communication série, baudrate 1500000)

## Notes de Développement

- **Architecture Hexagonale** : Ports & Adapters pattern
- **DDD** : Value Objects, Aggregates, Domain Services
- **Python 3.7+** : Compatibilité avec `Optional[type]` (pas de `type | None`)

