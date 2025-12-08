MOC :
Source : [[Luis Saluden]]
Projets : [[PROJET ASSOCE]] [[PROJET Banc de Test Python]]
Simulation :
Tags : #NoteAtomique
Date : 2025-05-23
***

# Guide des commandes - Système DDS/ADC

## Communication série
- **Paramètres**: 1.5 Mbaud, 8N1, timeout 2s
- **Format**: `aXX*` (adresse) puis `dYY*` (données)

## Tableau des adresses et commandes

### Paramètres DDS

| Paramètre | Adresses | Valeurs | Notes |
|-----------|----------|---------|-------|
| Fréquence | 62-63 | 0-65535 | Formule : `val = freq(Hz) * 2^32 / 16_000_000`<br>Adresse 62: MSB (16 bits haut)<br>Adresse 63: LSB (16 bits bas) |
| Mode | 39 | DDS1: 49 (AC), 1 (DC)<br>DDS2: 12544 (AC), 256 (DC) | Adresse 39: combinaison DDS1+DDS2<br>Exemple: 12593 = les deux en AC |
| Offset | 36-37 | 0-65535 | DDS1: @37, DDS2: @36 |
| Gain | 52-53 | 0-32768 | DDS1: @53, DDS2: @52 |
| Phase | 66-67 | 0-65535 | DDS1: @67, DDS2: @66 |
| Constante | 48-49 | 0-65535 | DDS1: @49, DDS2: @48 |

### Paramètres ADC

| Paramètre | Adresses | Valeurs | Notes |
|-----------|----------|---------|-------|
| CLKIN divider | 13 | 0-7 | Valeurs réelles: Reserved, 2, 4, 6, 8, 10, 12, 14<br>La valeur à envoyer est 0-7 (codage) |
| ICLK divider + Oversampling | 14 | Valeur combinée | Formule: (ICLK_code × 36) + Oversampling_code<br>ICLK_code (0-7): Reserved, 2, 4, 6, 8, 10, 12, 14<br>Oversampling_code (0-15): 4096→0, 2048→1, etc. |
| Références | 11 | Bitmask:<br>Neg. Ref: bit 7 (128)<br>High Res: bit 6 (64)<br>Ref V: bit 4 (16) - 0=2.442V, 1=4.0V<br>Ref Select: bit 3 (8) - 0=Ext, 1=Int | Configuration par masque de bits |
| Gain ADC | 17-20 | 0-4 (correspondant à 1, 2, 4, 8, 16) | Canal 1: @17, Canal 2: @18<br>Canal 3: @19, Canal 4: @20 |

## Oversampling ratio (codes)

| Valeur réelle | Code |
|---------------|------|
| 4096 | 0 |
| 2048 | 1 |
| 1024 | 2 |
| 800 | 3 |
| 768 | 4 |
| 512 | 5 |
| 400 | 6 |
| 384 | 7 |
| 256 | 8 |
| 200 | 9 |
| 192 | 10 |
| 128 | 11 |
| 96 | 12 |
| 64 | 13 |
| 48 | 14 |
| 32 | 15 |

## Exemples de commandes

### Régler la fréquence (32 bits)
```
a62*     # Adresse MSB
dXXXX*   # Valeur haute
a63*     # Adresse LSB
dYYYY*   # Valeur basse
```

### Configurer mode AC pour les deux DDS
```
a39*     # Adresse mode DDS1+DDS2
d12593*  # 49 (DDS1 en AC) + 12544 (DDS2 en AC)
```

### Configurer mode AC pour DDS1 et DC pour DDS2
```
a39*     # Adresse mode DDS1+DDS2
d305*    # 49 (DDS1 en AC) + 256 (DDS2 en DC)
```

### Configurer ICLK et Oversampling
```
a14*     # Adresse ICLK et Oversampling combinés
d38*     # ICLK=2 (code=1), Oversampling=4096 (code=0), 1×36+0=36
```

## Configurations rapides

### JSON par défaut
Utiliser le fichier `ADC_DDS_Configuration_Parameters.json` 

### LabVIEW prédéfini
Séquence d'initialisation compatible avec LabVIEW disponible. 