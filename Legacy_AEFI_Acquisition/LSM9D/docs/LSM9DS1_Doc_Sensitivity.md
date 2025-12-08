MOC :
Source : [[Luis Saluden]]
Projets : [[PROJET ASSOCE]] [[PROJET Banc de Test Python]]
Simulation :
Tags : #NoteAtomique
Date : 2025-06-10
***

# LSM9DS1 - Documentation de Sensibilité

## 📋 Vue d'Ensemble

Ce document détaille les méthodes de détermination de la sensibilité pour chaque capteur du LSM9DS1.

---

## 🚀 **Sensibilité de l'Accéléromètre Linéaire**

### 📐 **Principe de Mesure**

La sensibilité de l'accélération linéaire peut être déterminée, par exemple, en appliquant une accélération de **1 g** au dispositif.

### 🔄 **Procédure de Calibration**

1. **Positionnement Initial** 
   - Pointer l'axe sélectionné vers le sol
   - Noter la valeur de sortie

2. **Rotation et Mesure**
   - Faire pivoter le capteur de **180 degrés** (pointer vers le ciel)
   - Noter la nouvelle valeur de sortie

3. **Calcul de Sensibilité**
   - Appliquer l'accélération de **1 g** au capteur
   - Soustraire la valeur la plus grande de la plus petite
   - Diviser le résultat par **2** → **Sensibilité actuelle du capteur**

### 📊 **Caractéristiques**
- ✅ **Stabilité** : Cette valeur change très peu avec la température et le temps
- 📏 **Tolérance** : La tolérance de sensibilité décrit la plage de sensibilités d'un grand nombre de capteurs

---

## 🌀 **Sensibilité du Gyroscope à Vitesse Angulaire**

### ⚡ **Principe de Fonctionnement** 

Le gyroscope à vitesse angulaire est un dispositif qui produit une **sortie numérique positive** pour une rotation dans le sens des aiguilles d'une montre autour de l'axe considéré.

### 🎯 **Détermination de la Sensibilité**

- **Méthode** : Appliquer une vitesse angulaire définie au capteur
- **Calcul** : La sensibilité décrit le **gain du capteur**
- ✅ **Stabilité** : Cette valeur change très peu avec la température et le temps

### 📈 **Caractéristiques**
- **Direction** : Sortie positive = rotation horaire
- **Précision** : Sensibilité stable dans le temps
- **Fiabilité** : Peu d'influence des variations thermiques

---

## 🧲 **Sensibilité du Capteur Magnétique**

### 📡 **Principe de Mesure**

La sensibilité du capteur magnétique décrit le **gain du capteur** et peut être déterminée, par exemple, en appliquant un **champ magnétique de 1 gauss**.

### 🔧 **Méthode de Calibration**

1. **Application du Champ**
   - Appliquer un champ magnétique de référence (**1 gauss**)
   - Mesurer la réponse du capteur

2. **Calcul du Gain**
   - La sensibilité = Réponse mesurée / Champ appliqué
   - Unité typique : **LSB/gauss** (Least Significant Bit par gauss)

### 📊 **Caractéristiques**
- **Référence** : Champ magnétique de **1 gauss**
- **Application** : Détection et mesure de champs magnétiques
- **Gain** : Valeur exprimée en LSB/gauss

---

## 🎯 **Résumé des Sensibilités**

| **Capteur** | **Méthode de Référence** | **Unité de Mesure** | **Stabilité** |
|-------------|--------------------------|---------------------|---------------|
| 📐 **Accéléromètre** | 1 g (gravité terrestre) | LSB/g | ✅ Très stable |
| 🌀 **Gyroscope** | Vitesse angulaire définie | LSB/(°/s) | ✅ Très stable |
| 🧲 **Magnétomètre** | 1 gauss | LSB/gauss | ✅ Stable |

---

## 💡 **Points Clés à Retenir**

### ✅ **Stabilité Thermique**
- Toutes les sensibilités sont **peu affectées** par les variations de température
- **Dérive temporelle minimale** pour tous les capteurs

### 🔧 **Procédure de Calibration**
- **Accéléromètre** : Méthode de rotation 180° avec gravité
- **Gyroscope** : Application de vitesse angulaire contrôlée  
- **Magnétomètre** : Application de champ magnétique de référence

### 📏 **Tolérance de Production**
- La **tolérance de sensibilité** indique la variation entre différents capteurs de même modèle
- Important pour la **standardisation** et la **reproductibilité** des mesures

---

## 🔗 **Utilisation Pratique**

Cette documentation de sensibilité est **essentielle** pour :
- **Calibration** des capteurs en production
- **Conversion** des valeurs brutes en unités physiques
- **Compensation** des variations entre capteurs individuels
- **Validation** de la précision des mesures

---

*📅 Document basé sur la documentation technique officielle STMicroelectronics LSM9DS1* 