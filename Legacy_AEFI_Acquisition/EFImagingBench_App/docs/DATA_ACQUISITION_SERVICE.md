# DataAcquisitionService - Documentation

## 🎯 Vue d'ensemble

Le **DataAcquisitionService** est un nouveau service de la couche Application qui gère la **logique d'acquisition des données**, séparé de la configuration hardware qui reste dans `DeviceAcquisitionConfigService`.

## 📋 Responsabilités

### DataAcquisitionService (LOGIQUE d'acquisition)
- ✅ Contrôle du cycle de vie de l'acquisition (start/stop/pause/resume)
- ✅ Gestion du flux de données temps réel
- ✅ Moyennage des échantillons
- ✅ Statistiques d'acquisition (taux, durée, erreurs)
- ✅ Distribution des données aux abonnés (pattern Observer)
- ✅ Gestion du buffer de données

### DeviceAcquisitionConfigService (CONFIGURATION seulement)
- ⚙️ Configuration des paramètres ADC (gains, timing, référence)
- ⚙️ Configuration de l'export CSV (chemin, format, filtres)
- ⚙️ Validation des paramètres hardware
- ⚙️ Synchronisation configuration avec hardware

## 🔄 Séparation des préoccupations

```
┌─────────────────────────────────────────────────────────────┐
│                          GUI                                 │
└────────────┬──────────────────────────────┬─────────────────┘
             │                              │
             │ Config ADC/Export            │ Start/Stop/Data
             ▼                              ▼
┌────────────────────────────┐  ┌──────────────────────────────┐
│ DeviceAcquisitionConfig    │  │  DataAcquisitionService      │
│ Service                    │  │                              │
│                            │  │  - start_acquisition()       │
│ - set_adc_gain()           │  │  - stop_acquisition()        │
│ - set_adc_timing()         │  │  - get_latest_sample()       │
│ - start_csv_export()       │  │  - subscribe_data_updates()  │
│ - validate_config()        │  │  - get_acquisition_stats()   │
└────────────┬───────────────┘  └──────────────┬───────────────┘
             │                                 │
             │ Configuration                   │ Acquisition
             ▼                                 ▼
        ┌────────────────────────────────────────┐
        │      AcquisitionManager                │
        │      (Domain Layer)                    │
        └────────────────────────────────────────┘
```

## 📊 API Principale

### Contrôle Acquisition
```python
# Démarrer acquisition en mode exploration
service.start_acquisition(AcquisitionMode.EXPLORATION)

# Démarrer acquisition en mode export
service.start_acquisition(AcquisitionMode.EXPORT)

# Arrêter acquisition
service.stop_acquisition()

# Pause/Resume
service.pause_acquisition()
service.resume_acquisition()

# État
is_running = service.is_acquiring()
current_mode = service.get_current_mode()
```

### Accès aux données
```python
# Dernier échantillon
sample = service.get_latest_sample()
print(f"Channel 0: {sample.get_channel(0)}")

# Buffer d'échantillons
samples = service.get_sample_buffer(n_samples=100)

# Statistiques
stats = service.get_acquisition_stats()
print(f"Rate: {stats.samples_per_second} Hz")
print(f"Total: {stats.total_samples}")
```

### Observateurs (Pattern Observer)
```python
# S'abonner aux mises à jour de données
def on_new_data(sample: AcquisitionSample):
    print(f"New sample: {sample.channel_data}")

service.subscribe_data_updates(on_new_data)

# S'abonner aux changements de mode
def on_mode_change(mode: AcquisitionMode):
    print(f"Mode changed to: {mode}")

service.subscribe_mode_changes(on_mode_change)

# Se désabonner
service.unsubscribe_all(on_new_data)
```

## 🔄 Migration depuis MetaManager

### Code Legacy (MetaManager)
```python
# MetaManager (god object)
meta_manager.start_acquisition(mode="exploration", config={...})
meta_manager.stop_acquisition()
meta_manager._on_acquisition_data_ready(sample)
```

### Code Nouveau (Services séparés)
```python
# 1. Configuration (DeviceAcquisitionConfigService)
config_service.set_adc_gain(channel=0, gain=1)
config_service.set_averaging(n_avg=10)

# 2. Acquisition (DataAcquisitionService)
data_service.start_acquisition(AcquisitionMode.EXPLORATION)

# 3. Abonnement aux données
data_service.subscribe_data_updates(my_callback)

# 4. Arrêt
data_service.stop_acquisition()
```

## 📁 Fichiers

- **Diagramme**: `/docs/diagrams/application/data_acquisition_service_detailed.puml`
- **Implémentation**: `/src/application/data_acquisition_service.py` (à créer)
- **Tests**: `/tests/application/test_data_acquisition_service.py` (à créer)

## ✅ Avantages de la séparation

1. **Single Responsibility Principle (SRP)**
   - Chaque service a une responsabilité unique et claire
   
2. **Testabilité**
   - Configuration et acquisition peuvent être testées indépendamment
   
3. **Réutilisabilité**
   - DataAcquisitionService peut être utilisé avec différentes configurations
   - DeviceAcquisitionConfigService peut valider sans démarrer l'acquisition
   
4. **Maintenabilité**
   - Modifications de configuration n'impactent pas la logique d'acquisition
   - Modifications du flux de données n'impactent pas la configuration

## 🔗 Relations avec autres services

- **DeviceExcitationConfigService**: Configure le DDS (excitation)
- **DeviceAcquisitionConfigService**: Configure l'ADC et l'export
- **DataAcquisitionService**: Utilise la config pour acquérir les données
- **ScanService**: Orchestre DataAcquisitionService pour les scans 2D
- **MotionService**: Indépendant, gère uniquement le mouvement

## 📝 Notes importantes

- ⚠️ **DeviceAcquisitionConfigService** ne démarre PAS l'acquisition
- ⚠️ **DataAcquisitionService** n'a PAS de méthodes de configuration ADC
- ✅ Les deux services communiquent avec `AcquisitionManager` mais pour des responsabilités différentes
- ✅ Pattern Observer pour découpler GUI et logique métier
