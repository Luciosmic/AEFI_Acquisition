MOC :
Source : [[Luis Saluden]]
Projets : [[PROJET ASSOCE]] [[PROJET Banc de Test Python]]
Simulation :
Tags : #NoteAtomique
Date : 2025-05-23
***

# Documentation du Banc de Détection Synchrone

## Introduction

Ce document décrit la structure et l'utilisation du fichier de configuration JSON (`ADC_DDS_Configuration_Parameters.json`) qui permet de piloter un banc de détection synchrone comprenant :

- **AD9106** : Générateur 4 canaux DDS/DAC pour l'excitation et la référence
- **ADS131A04** : Convertisseur analogique-numérique 4 canaux pour l'acquisition

Le système implémente une détection synchrone permettant d'extraire des signaux faibles noyés dans le bruit en utilisant une référence de phase cohérente avec l'excitation.

## Architecture du Système

```
DDS1+DDS2 (AD9106) → Signaux d'excitation → EXPÉRIENCE → Signaux modifiés
     ↓ (180° déphasage)                                        ↓
 Référence de                                          Détection synchrone
  phase commune                                               ↑
     ↓                                              DDS3+DDS4 (AD9106)
ADS131A04 (ADC) ← Signaux détectés ← Détecteur synchrone ← Référence
       ↓
 Amplitude + Phase
```

## Principe de Fonctionnement

### 1. Excitation différentielle
- DDS1 et DDS2 génèrent des signaux en opposition de phase (180°)
- Cette configuration différentielle améliore le rapport signal/bruit
- Les signaux d'excitation stimulent l'expérience à étudier

### 2. Modulation par l'expérience
- L'expérience modifie l'amplitude et la phase des signaux d'excitation
- Ces modifications contiennent l'information physique d'intérêt

### 3. Détection synchrone
- DDS3 et DDS4 fournissent les références pour la détection synchrone
- Le détecteur synchrone multiplie le signal modifié par la référence
- Seuls les signaux cohérents avec la référence sont conservés

### 4. Acquisition numérique
- ADS131A04 numérise les signaux issus de la détection synchrone
- Extraction de l'amplitude et de la phase du signal d'intérêt
- Rejection du bruit non-corrélé

## Structure du Fichier JSON

Le fichier est organisé en deux sections principales :

```json
{
  "ADC": {
    // Configuration ADS131A04 - Acquisition
  },
  "DDS": {
    // Configuration AD9106 - Génération DDS/DAC
  }
}
```

### Section ADC (ADS131A04)

Configuration du convertisseur analogique-numérique pour l'acquisition des signaux de détection synchrone :

```json
"ADC": {
  "References_Configuration": { 
    "adresse": 11, 
    "valeur": 96,
    "description": "A_SYS_CFG: HRM=1, VREF=2.442V, INT_REF=0" 
  },
  "CLK1_Configuration": { 
    "adresse": 13, 
    "valeur": 8,
    "description": "CLK1: CLK_DIV=8 (fICLK = fCLKIN/8)" 
  },
  "CLK2_Configuration": { 
    "adresse": 14, 
    "valeur": 134,
    "description": "CLK2: ICLK_DIV=8 + OSR=32" 
  },
  "Gain_ADC_1": { "adresse": 17, "valeur": 0, "options": [0, 1, 2, 3, 4] },
  "Gain_ADC_2": { "adresse": 18, "valeur": 0, "options": [0, 1, 2, 3, 4] },
  "Gain_ADC_3": { "adresse": 19, "valeur": 0, "options": [0, 1, 2, 3, 4] },
  "Gain_ADC_4": { "adresse": 20, "valeur": 0, "options": [0, 1, 2, 3, 4] }
}
```

**Mapping des gains ADC :**
- 0 = Gain ×1 (défaut)
- 1 = Gain ×2  
- 2 = Gain ×4
- 3 = Gain ×8
- 4 = Gain ×16

### Section DDS (AD9106)

Configuration du générateur DDS/DAC pour l'excitation et la référence :

```json
"DDS": {
  "Frequence_DDS": { 
    "adresse": [62, 63], 
    "valeur": 1000, 
    "min": 0, 
    "max": 4294967295,
    "description": "Fréquence commune à tous les DDS (Hz)"
  },
  "Mode_DDS1_DDS2": { 
    "adresse": 39, 
    "valeur": 12593,
    "description": "Mode AC pour DDS1+DDS2 (excitation)" 
  },
  "Mode_DDS3_DDS4": { 
    "adresse": 38, 
    "valeur": 12593,
    "description": "Mode AC pour DDS3+DDS4 (référence)" 
  },
  "Phase_DDS1": { "adresse": 67, "valeur": 0, "description": "Phase DDS1 (0°)" },
  "Phase_DDS2": { "adresse": 66, "valeur": 32768, "description": "Phase DDS2 (180°)" },
  "Phase_DDS3": { "adresse": 65, "valeur": 0, "description": "Phase DDS3 (0°)" },
  "Phase_DDS4": { "adresse": 64, "valeur": 16384, "description": "Phase DDS4 (90°)" },
  
  "Gain_DAC1": { "adresse": 53, "valeur": 1024, "max": 2047, "description": "Gain numérique DAC1" },
  "Gain_DAC2": { "adresse": 52, "valeur": 1024, "max": 2047, "description": "Gain numérique DAC2" },
  "Gain_DAC3": { "adresse": 51, "valeur": 1024, "max": 2047, "description": "Gain numérique DAC3" },
  "Gain_DAC4": { "adresse": 50, "valeur": 1024, "max": 2047, "description": "Gain numérique DAC4" },
  "Offset_DAC1": { "adresse": 37, "valeur": 0, "description": "Offset DC DAC1" },
  "Offset_DAC2": { "adresse": 36, "valeur": 0, "description": "Offset DC DAC2" },
  "Offset_DAC3": { "adresse": 35, "valeur": 0, "description": "Offset DC DAC3" },
  "Offset_DAC4": { "adresse": 34, "valeur": 0, "description": "Offset DC DAC4" }
}
```

## Rôles des Canaux DDS

### Canaux d'excitation (DDS1 + DDS2)
- **DDS1** : Signal d'excitation phase 0°
- **DDS2** : Signal d'excitation phase 180° (opposition)
- **Configuration différentielle** pour améliorer le rapport signal/bruit
- **Fréquence** : Fréquence de résonance de l'expérience

### Canaux de référence (DDS3 + DDS4)  
- **DDS3** : Référence en phase (0°) pour détection synchrone
- **DDS4** : Référence en quadrature (90°) pour détection synchrone
- **Cohérence de phase** avec l'excitation pour la corrélation
- **Même fréquence** que l'excitation

## Configuration Typique pour Détection Synchrone

### Excitation différentielle optimale

```python
# Fréquence d'excitation (exemple : 1 kHz)
DDS_frequency = 1000  # Hz

# Excitation en opposition de phase
DDS1_phase = 0      # 0° - Signal d'excitation A
DDS2_phase = 32768  # 180° - Signal d'excitation B (opposition)

# Référence pour détection synchrone  
DDS3_phase = 0      # 0° - Référence en phase
DDS4_phase = 16384  # 90° - Référence en quadrature

# Gains équilibrés
DAC1_gain = DAC2_gain = 1024  # Excitation équilibrée
DAC3_gain = DAC4_gain = 1024  # Référence équilibrée
```

## Calcul de la Fréquence DDS

### Formule de conversion

```
Valeur_32bits = (Fréquence_Hz / 16000000) × 2^32
```

Où :
- **16000000** Hz = Fréquence de l'oscillateur AD9106
- **2^32** = Résolution du calcul DDS (4294967296)

### Répartition sur les registres

```python
# Exemple pour 1000 Hz
valeur_32bits = int((1000 / 16000000) * 4294967296)  # ≈ 268435456

# Séparation en 16 bits
MSB = (valeur_32bits >> 16) & 0xFFFF  # Adresse 62
LSB = valeur_32bits & 0xFFFF          # Adresse 63
```

### Exemples de fréquences courantes

| Fréquence | Valeur 32-bit | MSB (addr 62) | LSB (addr 63) |
|-----------|---------------|---------------|---------------|
| 100 Hz    | 26843546      | 409          | 33162         |
| 1 kHz     | 268435456     | 4096         | 0             |
| 10 kHz    | 2684354560    | 40960        | 0             |

## Configuration des Gains ADC

### Optimisation de la dynamique

```python
# Pour signaux faibles de détection synchrone
ADC_gains = {
    "canal_1": 4,  # ×16 pour signaux µV
    "canal_2": 4,  # ×16 pour signaux µV  
    "canal_3": 2,  # ×4 pour signaux mV
    "canal_4": 0   # ×1 pour signaux V
}
```

### Calcul de la résolution effective

```
Résolution_effective = VREF / (2^24 × Gain_ADC)
```

Exemples avec VREF = 2.442V :
- Gain ×1 : 145 nV/LSB
- Gain ×16 : 9 nV/LSB

## Format des Commandes Série

### Séquence de configuration

```
a<adresse>*    # Sélectionne l'adresse
d<valeur>*     # Envoie la valeur
```

### Exemple complet : Configuration 1kHz différentielle

```python
# Fréquence DDS : 1000 Hz
a62*d4096*     # MSB fréquence
a63*d0*        # LSB fréquence

# Modes AC pour tous les DDS
a39*d12593*    # DDS1+DDS2 en mode AC
a38*d12593*    # DDS3+DDS4 en mode AC

# Phases pour excitation différentielle
a67*d0*        # DDS1 : 0°
a66*d32768*    # DDS2 : 180°
a65*d0*        # DDS3 : 0° (référence)
a64*d16384*    # DDS4 : 90° (quadrature)

# Gains équilibrés
a53*d1024*     # Gain DAC1
a52*d1024*     # Gain DAC2
a51*d1024*     # Gain DAC3  
a50*d1024*     # Gain DAC4
```

## Registres de Configuration Détaillés

### Registres ADS131A04 (ADC)

| Adresse | Nom | Description | Valeurs possibles |
|---------|-----|-------------|-------------------|
| 11 | A_SYS_CFG | Configuration analogique | HRM, VREF, INT_REFEN |
| 13 | CLK1 | Configuration horloge 1 | CLK_DIV[2:0] |
| 14 | CLK2 | Configuration horloge 2 | ICLK_DIV[2:0] + OSR[3:0] |
| 17-20 | ADC1-ADC4 | Gains canaux ADC | 0-4 (×1 à ×16) |

### Registres AD9106 (DDS/DAC)

| Adresse | Nom | Description | Plage |
|---------|-----|-------------|-------|
| 62 | DDS_TW32 | Fréquence MSB | 0-65535 |
| 63 | DDS_TW1 | Fréquence LSB | 0-65535 |
| 38 | DDSx_CONFIG | Mode DDS3+DDS4 | AC/DC |
| 39 | DDSx_CONFIG | Mode DDS1+DDS2 | AC/DC |
| 64-67 | DDSx_PW | Phases DDS1-4 | 0-65535 (0-360°) |
| 50-53 | DACx_DGAIN | Gains DAC1-4 | 0-2047 |
| 34-37 | DACx_DOF | Offsets DAC1-4 | ±50% FSR |

## Procédure de Calibration

### 1. Test de cohérence des DDS

```python
# Vérifier que DDS1 et DDS2 sont bien en opposition
# Vérifier que DDS3 et DDS4 sont bien en quadrature
# Mesurer les amplitudes relatives
```

### 2. Optimisation des gains ADC

```python
# Ajuster selon l'amplitude des signaux détectés
# Maximiser la dynamique sans saturation
# Équilibrer les canaux I et Q
```

### 3. Validation du système complet

```python
# Test avec signal de référence connu
# Vérification amplitude/phase mesurée vs théorique
# Test de stabilité temporelle
```

## Conseils d'Utilisation

### 1. Cohérence de phase
- Maintenir la relation de phase entre excitation et référence
- Éviter les reconfiguration partielles des DDS
- Synchroniser les modifications de fréquence

### 2. Optimisation du rapport S/B
- Utiliser l'excitation différentielle (180°)
- Ajuster les gains ADC selon l'amplitude détectée
- Filtrer numériquement après acquisition

### 3. Stabilité du système
- Laisser stabiliser après changement de fréquence
- Monitorer la température pour la stabilité des DDS
- Calibrer régulièrement avec signal test

### 4. Debugging
- Vérifier d'abord les signaux d'excitation
- Contrôler les références de détection synchrone
- Valider les gains ADC avec signaux test

## Calcul de la Fréquence d'Échantillonnage ADC

La fréquence d'échantillonnage de l'ADS131A04 dépend de plusieurs paramètres :

```
Fe = fCLKIN / (CLK_DIV × ICLK_DIV × OSR)
```

Où :
- **fCLKIN** = 16 MHz (fréquence d'entrée)
- **CLK_DIV** = Diviseur d'horloge (bits 3:1 du registre 13)
- **ICLK_DIV** = Diviseur ICLK (bits 7:5 du registre 14)
- **OSR** = Ratio de suréchantillonnage (bits 3:0 du registre 14)

### Exemple de calcul

```python
# Configuration par défaut
fCLKIN = 16000000  # 16 MHz
CLK_DIV = 8        # Registre 13, valeur 4 → diviseur 8
ICLK_DIV = 8       # Registre 14, valeur 4 → diviseur 8  
OSR = 400          # Registre 14, valeur 6 → OSR 400

# Calcul de la fréquence d'échantillonnage
Fe = 16000000 / (8 * 8 * 400) = 6250 Hz
```

## Baudrate de Communication

**Baudrate recommandé :** 1 500 000 bauds (1.5 Mbaud)

Ce baudrate optimise la vitesse de configuration tout en maintenant la fiabilité de la communication série.

## Dépannage

### Problèmes fréquents

| Symptôme | Cause probable | Solution |
|----------|----------------|----------|
| Pas de signal DDS | Mode DC au lieu d'AC | Vérifier registres 38/39 |
| Mauvaise phase | Valeurs de phase incorrectes | Vérifier registres 64-67 |
| Saturation ADC | Gain trop élevé | Réduire gain ADC (reg 17-20) |
| Bruit important | Gains déséquilibrés | Équilibrer gains DAC/ADC |

### Séquence de test

1. **Test DDS individuels** : Vérifier chaque sortie DDS
2. **Test phases relatives** : Mesurer déphasages 180° et 90°
3. **Test chaîne complète** : Signal connu → détection → mesure
4. **Optimisation** : Ajuster gains pour SNR optimal

---

*Cette documentation correspond à un banc de détection synchrone utilisant AD9106 (génération) + ADS131A04 (acquisition) avec excitation différentielle et référence en quadrature.*