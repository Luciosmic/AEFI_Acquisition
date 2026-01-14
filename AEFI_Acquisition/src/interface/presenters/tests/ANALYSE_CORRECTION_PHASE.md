# Analyse de la Correction de Phase

## Vue d'ensemble

La correction de phase dans `SignalPostProcessor` permet d'aligner les vecteurs (I, Q) sur l'axe In-Phase (I) en effectuant une rotation dans le plan complexe.

## Implémentation

### Principe

1. **Calibration** : On calcule l'angle θ du vecteur de référence avec `atan2(Q, I)`
2. **Rotation** : On applique une rotation de `-θ` pour aligner le vecteur sur l'axe I

### Formule mathématique

Pour un vecteur (I, Q) et un angle de rotation θ :

```
I' = I cos(θ) + Q sin(θ)
Q' = -I sin(θ) + Q cos(θ)
```

Cette formule correspond à une rotation de `-θ` dans le plan complexe.

### Code source

```python
# Calcul de l'angle (ligne 106)
theta = math.atan2(q, i)

# Application de la rotation (lignes 67-68)
i_new = i_val * cos_t + q_val * sin_t
q_new = -i_val * sin_t + q_val * cos_t
```

## Propriétés mathématiques

### Préservation de la magnitude

La rotation est une transformation orthogonale, donc :
- La magnitude du vecteur est préservée : `√(I² + Q²) = √(I'² + Q'²)`
- Le déterminant de la matrice de rotation est 1

### Alignement sur l'axe I

Après correction avec un vecteur de référence (I_ref, Q_ref) :
- Le vecteur de référence devient (√(I_ref² + Q_ref²), 0)
- Tous les autres vecteurs sont également tournés de `-θ`

## Problèmes potentiels identifiés

### 1. Calibration multi-axes

**Problème** : La méthode `calibrate_phase()` traite tous les axes simultanément. Si on passe seulement les valeurs pour un axe, les autres axes sont à 0, ce qui donne `atan2(0, 0) = 0` et écrase les valeurs précédentes.

**Solution** : Toujours passer toutes les valeurs pour tous les axes lors de la calibration.

### 2. Vecteur nul

**Problème** : Si le vecteur de référence est (0, 0), `atan2(0, 0) = 0`, ce qui peut donner des résultats inattendus.

**Solution** : Vérifier que le vecteur de référence n'est pas nul avant la calibration.

### 3. Ordre des opérations

La correction de phase doit être appliquée :
1. **Après** la soustraction du bruit (noise correction)
2. **Avant** la soustraction du champ primaire (primary field subtraction)

## Tests robustes

Le fichier `test_phase_correction_robust.py` contient 8 tests qui vérifient :

1. **Rotation de base** : Vecteur à 45° aligné sur l'axe I
2. **Vecteurs analytiques** : Test avec plusieurs angles prédéfinis
3. **Propriétés de la matrice de rotation** : Préservation de la magnitude, orthogonalité
4. **Plusieurs vecteurs avec la même calibration** : Vérification de la cohérence
5. **Vecteur nul** : Gestion du cas limite
6. **Tous les axes** : Correction indépendante pour chaque axe
7. **Recalibration séquentielle** : Vérification que la recalibration écrase la précédente
8. **Vérification analytique** : Comparaison avec le calcul manuel

## Recommandations

1. **Utiliser des fonctions analytiques** pour les tests (cos, sin) plutôt que des données réelles
2. **Vérifier la magnitude** après correction pour détecter les erreurs
3. **Tester les cas limites** : vecteurs nuls, angles multiples de 90°, etc.
4. **Documenter l'ordre des opérations** : noise → phase → primary

## Exemple d'utilisation

```python
processor = SignalPostProcessor()

# 1. Calibrer avec un vecteur de référence
ref_sample = {
    "Ux In-Phase": 1.0,
    "Ux Quadrature": 1.0,  # 45°
    "Uy In-Phase": 0.0,
    "Uy Quadrature": 0.0,
    "Uz In-Phase": 0.0,
    "Uz Quadrature": 0.0,
}
processor.calibrate_phase(ref_sample)

# 2. Traiter les échantillons
sample = {
    "Ux In-Phase": 0.0,
    "Ux Quadrature": 1.0,  # 90°
    # ... autres axes
}
processed = processor.process_sample(sample)

# Après correction, le vecteur (0, 1) devient aligné sur I
# avec un angle relatif de 90° - 45° = 45°
```
