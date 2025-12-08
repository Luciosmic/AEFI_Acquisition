Le facteur de conversion, **cf=4.76837E-7**,  est **crucial** pour votre banc d'acquisition. Ce facteur  correspond exactement à la résolution de votre ADS131A04. Je vais vous expliquer d'où il vient.

## 🧮 **CALCUL DU FACTEUR DE CONVERSION**

### **Formule officielle de l'ADS131A04**
```
1 LSB = (2 × VREF / Gain) / 2^24
```

### **Avec vos paramètres**
D'après votre configuration JSON :
- **VREF = 4.0V** (VREF_4V = 1)
- **Gain = 1** (pour tous les ADCs)
- **Résolution = 24 bits**

### **Calcul exact**
```
1 LSB = (2 × 4.0V / 1) / 2^24
1 LSB = 8.0V / 16777216
1 LSB = 4.76837158203125E-7 V
```

**✅ Votre facteur 4.76837E-7 est PARFAITEMENT CORRECT !**

---

## 📊 **SIGNIFICATION PRATIQUE**

### **Résolution de mesure**
- **1 LSB = 0.476837 µV** 
- **Plage totale = ±4.0V** (de -4V à +4V)
- **Codes ADC = -8388608 à +8388607** (24 bits signés)

### **Conversion code → tension**
```
Tension (V) = Code_ADC × 4.76837E-7
```

### **Exemples pratiques**
```
Code = 8388607  → +4.0V (pleine échelle positive)
Code = 0        → 0V (zéro)
Code = -8388608 → -4.0V (pleine échelle négative)
Code = 1000000  → 0.477V
Code = -500000  → -0.238V
```

---

## ⚙️ **OPTIMISATION SELON VOTRE SIGNAL**

Si vos signaux sont plus petits, vous pouvez **augmenter le gain** pour améliorer la résolution :

| Gain | Plage | Résolution LSB | Usage |
|------|-------|----------------|--------|
| **1** | ±4.0V | 0.477 µV | **Signaux large bande** |
| **2** | ±2.0V | 0.238 µV | Signaux moyens |
| **4** | ±1.0V | 0.119 µV | Signaux précis |
| **8** | ±0.5V | 0.060 µV | **Très haute précision** |
| **16** | ±0.25V | 0.030 µV | Signaux très faibles |

---

## 🔧 **VALIDATION DE VOTRE CONFIGURATION**

Votre setup est **optimal** pour :
- ✅ **Signaux haute amplitude** (jusqu'à ±4V)
- ✅ **Résolution maximum** sur large plage
- ✅ **Référence stable** (dérive 6ppm/°C)
- ✅ **Signaux négatifs** (charge pump activée)

**Cette configuration de 4.76837E-7 V/LSB vous donne une précision exceptionnelle sur une large plage !**

Voulez-vous que je vous aide à optimiser le gain selon vos signaux spécifiques ?