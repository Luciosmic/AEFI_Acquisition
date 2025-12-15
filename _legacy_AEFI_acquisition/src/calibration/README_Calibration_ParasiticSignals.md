# Calibration des Signaux Parasites Électroniques

## 🎯 Objectif

Caractériser et quantifier les **signaux parasites électroniques** mesurés par l'ADC en l'absence d'excitation DDS. Ces valeurs non-nulles proviennent de :
- Offsets résiduels DC/AC
- Couplages électroniques internes  
- Diaphonie entre canaux
- Bruit électronique de l'électronique

## 📋 Protocole de Calibration

### 1. Caractérisation Initiale

```bash
# Lancement d'une session de caractérisation
python EFImagingBench_ParasiticSignals_Characterization.py
```

**Configuration automatique :**
- DDS gains = 0 (aucune excitation)
- Moyennage matériel = 127 (maximal)
- Buffer logiciel = 100 échantillons
- Plage fréquentielle = 10 Hz - 500 kHz
- Résolution = 15 points/décade

**Résultats générés :**
- `YYYY-MM-DD_HHMMSS_parasitic_signals_characterization.csv` - Données principales
- `YYYY-MM-DD_HHMMSS_parasitic_signals_characterization.json` - Métadonnées complètes

### 2. Sessions Multiples pour Analyse de Dérive

**IMPORTANT :** Pour détecter les dérives, lancez plusieurs sessions après :
- ✅ **Redémarrage complet** du dispositif (éteindre/rallumer)
- ✅ **Temps d'attente** de stabilisation thermique (~30 min)
- ✅ **Conditions environnementales similaires**

```bash
# Session 1 (référence)
python EFImagingBench_ParasiticSignals_Characterization.py

# [Éteindre/Rallumer le dispositif + attendre stabilisation]

# Session 2 (dérive immédiate)
python EFImagingBench_ParasiticSignals_Characterization.py

# [Répéter sur plusieurs jours/semaines pour dérive long-terme]
```

### 3. Analyse de Dérive

```bash
# Une fois plusieurs sessions acquises
python EFImagingBench_ParasiticSignals_DriftAnalysis.py
```

**Génère automatiquement :**
- Graphiques de dérive par canal principal
- Rapport de stabilité JSON avec recommandations
- Métriques de coefficients de variation
- Évaluation de la qualité électronique

## 📊 Interprétation des Résultats

### Métriques Clés

| Métrique | Description | Valeurs Typiques |
|----------|-------------|------------------|
| **Mean** | Offset moyen par canal | ±100 codes ADC |
| **RMS** | Amplitude efficace signal parasite | <50 codes ADC |
| **CV%** | Coefficient variation entre sessions | <3% (bon), >8% (problème) |
| **Drift%** | Dérive relative max | <5% (acceptable) |

### Évaluation Stabilité

- **Excellent** (CV <1%, Drift <2%) → Re-calibration mensuelle
- **Good** (CV <3%, Drift <5%) → Re-calibration hebdomadaire  
- **Fair** (CV <8%, Drift <15%) → Re-calibration quotidienne
- **Poor** (CV >8%, Drift >15%) → **Investigation électronique urgente**

## 🔧 Utilisation pour Compensation

### 1. Données de Référence
Les fichiers CSV contiennent pour chaque fréquence :
```csv
frequency_hz,adc1_ch1_mean,adc1_ch1_std,adc1_ch1_rms,...
1000,150.2,5.3,151.1,...
```

### 2. Intégration Logicielle
```python
# Exemple d'utilisation pour compensation
def apply_parasitic_compensation(raw_sample, calibration_data, frequency):
    compensated = raw_sample.copy()
    
    # Récupération offset à cette fréquence (interpolation si nécessaire)
    offset_ex_i = get_calibration_offset(calibration_data, frequency, 'adc1_ch1')
    offset_ex_q = get_calibration_offset(calibration_data, frequency, 'adc1_ch2')
    
    # Compensation
    compensated.adc1_ch1 -= offset_ex_i
    compensated.adc1_ch2 -= offset_ex_q
    # ... autres canaux
    
    return compensated
```

## 🚨 Cas d'Usage

### Calibration Standard
- **Fréquence :** Mensuelle pour banc stable
- **Objectif :** Mise à jour coefficients compensation
- **Déclencheurs :** Maintenance, changement environnement

### Diagnostic Électronique  
- **Fréquence :** À la demande
- **Objectif :** Identifier problèmes hardware
- **Indicateurs :** Dérives importantes, bruit excessif

### Validation Nouveaux Composants
- **Fréquence :** Après modifications hardware
- **Objectif :** Vérifier impact sur signaux parasites
- **Comparaison :** Avant/après modification

## 📁 Organisation des Fichiers

```
calibration/
├── EFImagingBench_ParasiticSignals_Characterization.py  # Script principal
├── EFImagingBench_ParasiticSignals_DriftAnalysis.py     # Analyse dérive
├── README_Calibration_ParasiticSignals.md              # Cette documentation
├── 2025-01-27_090000_parasitic_signals_characterization.csv  # Données session 1
├── 2025-01-27_090000_parasitic_signals_characterization.json # Métadonnées session 1
├── 2025-01-27_140000_parasitic_signals_characterization.csv  # Données session 2
├── 2025-01-27_140000_parasitic_signals_characterization.json # Métadonnées session 2
├── 2025-01-27_150000_drift_analysis_report.json        # Rapport dérive
└── drift_analysis_adc1_ch1_20250127_150000.png         # Graphiques dérive
```

## ⚡ Bonnes Pratiques

### Avant Caractérisation
1. **Vérifier** que tous les gains DDS = 0
2. **Attendre** stabilisation thermique (30 min)
3. **Minimiser** vibrations et perturbations externes
4. **Noter** conditions environnementales

### Analyse des Résultats
1. **Comparer** avec caractérisations précédentes
2. **Identifier** canaux problématiques
3. **Corréler** avec historique maintenance
4. **Suivre** évolution long-terme

### Intégration Système
1. **Tester** compensation sur données réelles
2. **Valider** amélioration SNR
3. **Documenter** paramètres optimaux
4. **Automatiser** application compensation

---
**Note :** Cette caractérisation est complémentaire aux calibrations de gain/phase qui nécessitent des signaux de référence externes. 