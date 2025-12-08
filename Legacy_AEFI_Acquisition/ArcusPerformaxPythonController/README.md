# ArcusPerformaxPythonController

## Objectif

Ce projet propose une interface Python moderne et modulaire pour piloter un contrôleur Arcus Performax 4EX (banc de test XY), avec une interface graphique permettant le contrôle précis des moteurs en position.

## État du projet

✅ **FONCTIONNEL** - Interface graphique opérationnelle permettant le contrôle complet des moteurs X et Y en position.

## Architecture

- `controller/EFImagingBench_Controller_ArcusPerformax4EXStage.py` : Contrôleur principal pour banc d'imagerie - Logique de pilotage du contrôleur Arcus (moteurs, homing, vitesses, protection par butées)
- `gui/EFImagingBench_Interface_ArcusPerformax4EXStage.py` : Interface graphique (Tkinter) pour piloter les axes X et Y avec contrôle en position
- `docs/PylablibDoc_ArcusPackage_SourceCode.py` : Documentation complète du code source pylablib pour référence
- `controller/DLL64/` : DLLs nécessaires (PerformaxCom.dll, SiUSBXp.dll)

## Fonctionnalités validées

- ✅ **Homing automatique** des axes X et Y (direction négative, home input)
- ✅ **Déplacement en position absolue** avec protection par homing obligatoire
- ✅ **Configuration des vitesses** (LS, HS, ACC, DEC) pour chaque axe
- ✅ **Arrêt d'urgence** (immédiat ou progressif)
- ✅ **Monitoring en temps réel** des positions
- ✅ **Interface intuitive** inspirée de LabVIEW

## Installation

1. **Python 3.7+ 64 bits**
2. Installer les dépendances :
   ```bash
   pip install pylablib
   pip install PyQt5
   ```
3. Placer les DLLs Arcus 64 bits dans le dossier `controller/DLL64/` et adapter le chemin dans le code si besoin.

## Utilisation

### Lancement de l'interface graphique
```bash
python gui/EFImagingBench_Interface_ArcusPerformax4EXStage.py
```

### Workflow typique
1. **Homing** : Cliquer sur "HOME" pour chaque axe (X, Y) - obligatoire avant tout déplacement
2. **Configuration vitesses** : Ajuster LS, HS, ACC, DEC puis cliquer "SET ACC & SPEEDS"
3. **Déplacement** : Entrer la position cible et cliquer "MOVE TO"
4. **Arrêt** : Boutons rouge pour arrêt progressif ou immédiat

## Philosophie de développement

- **Séparation stricte** entre la logique de commande (controller) et l'interface graphique (gui)
- **Sécurité** : Protection par homing obligatoire et butées hardware
- **Robustesse** : Utilisation des méthodes pylablib natives pour plus de fiabilité
- **Extensible** : facile d'ajouter un module d'acquisition de données (DDS, etc.)
- **Documentation** : chaque module est commenté, le code est prêt à être repris par un autre développeur

## Pour aller plus loin

- Le fichier `docs/PylablibDoc_StagesControlBasics.md` pour maîtriser les concepts fondamentaux du contrôle de platines (homing, mouvement asynchrone, gestion des axes)
- Voir le fichier `docs/PylablibDoc_ArcusPackage_SourceCode.py` pour la documentation technique détaillée du code source pylablib associée au fichier suivant
- Consulter `docs/PylablibDoc_ArcusPackage.md` pour la documentation complète de l'API pylablib.devices.Arcus avec tous les paramètres et méthodes disponibles
- Lire `docs/PylablibDoc_ArcusPerformax.md` pour comprendre les spécificités des contrôleurs Arcus Performax (modes de communication, gestion des erreurs, configuration multi-axes)

- Possibilité d'intégrer d'autres modules (acquisition, synchronisation, etc.) grâce à l'architecture modulaire 