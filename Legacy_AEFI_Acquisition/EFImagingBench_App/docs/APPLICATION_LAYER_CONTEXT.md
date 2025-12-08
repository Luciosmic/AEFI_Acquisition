# Contexte : Migration vers Application Layer

## 🎯 Objectif
Remplacer progressivement le **MetaManager** (god object) par une **couche Application** découpée en 4 services respectant SOLID/DDD.

## 📦 Architecture actuelle (Legacy)
```
GUI → MetaManager → StageManager/AcquisitionManager → Controllers
```

**Problème :** MetaManager = god object avec trop de responsabilités

## 🏗️ Architecture cible
```
GUI → Application Layer (4 services) → Managers → Controllers
```

## 5 Services de la couche Application

| Service | Responsabilité | Remplace MetaManager |
|---------|---------------|---------------------|
| **MotionService** | Mouvement axes X/Y | `move_to()`, `home()`, `stop()` |
| **ScanService** | Scans 2D + Export | `inject_scan_batch()`, `start_export_csv()` |
| **DeviceExcitationConfigService** | Config DDS (4 canaux) | `update_configuration()` pour DDS |
| **DeviceAcquisitionConfigService** | Config ADC + Export | Config ADC, paramètres export |
| **DataAcquisitionService** | Acquisition données | `start_acquisition()`, `stop_acquisition()`, flux données |

### Séparation des responsabilités Acquisition

**DeviceAcquisitionConfigService** (Configuration SEULEMENT)
- Configuration des paramètres ADC (gains, timing, référence)
- Configuration de l'export CSV (chemin, format, filtres)
- Validation des paramètres hardware
- Synchronisation configuration avec hardware

**DataAcquisitionService** (Logique d'acquisition SEULEMENT)
- Contrôle du cycle de vie acquisition (start/stop/pause)
- Gestion du flux de données temps réel
- Moyennage des échantillons
- Statistiques d'acquisition
- Distribution des données aux abonnés (GUI, export)


## 📋 Stratégie de migration
1. ✅ Créer diagrammes PlantUML (voir `/docs/diagrams/application/`)
2. ⏳ Implémenter services vides
3. ⏳ Copier logique MetaManager → Services
4. ⏳ Migrer GUI progressivement
5. ⏳ Supprimer MetaManager

## 🚫 Simplifications
- **Pas de post-processing** pour l'instant (retiré des diagrammes)
- Focus sur migration minimale pour avoir une acquisition fonctionnelle aujourd'hui

## 📁 Fichiers clés
- `/docs/diagrams/application/application_layer.puml` - Vue générale
- `/docs/diagrams/application/*_detailed.puml` - API de chaque service
- `/src/application/` - Implémentation des services (à créer)
- `/src/gui/EFImagingBench_GUI.py` - GUI à migrer progressivement

## 💡 Prompt de démarrage suggéré
```
Je travaille sur la migration du MetaManager vers une Application Layer.
Contexte dans @APPLICATION_LAYER_CONTEXT.md
Diagrammes dans @docs/diagrams/application/

Objectif : [décrire la tâche spécifique]
```

