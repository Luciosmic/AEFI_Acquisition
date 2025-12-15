# Correction Critique : Rotations Extrinsèques vs Intrinsèques

## Problème Identifié

Le code utilisait des **rotations intrinsèques** (axes mobiles du capteur) au lieu de **rotations extrinsèques** (axes fixes du laboratoire).

### Comportement Incorrect (Avant)
```python
# 'xyz' (minuscules) = rotations intrinsèques
R.from_euler('xyz', [theta_x, theta_y, theta_z], degrees=True)
```

**Effet** :
1. Rotation de `theta_x` autour de **X du capteur**
2. Rotation de `theta_y` autour de **Y du capteur** (déjà tourné par X)
3. Rotation de `theta_z` autour de **Z du capteur** (déjà tourné par X et Y)

❌ **Problème** : Les axes de référence changent à chaque rotation, rendant l'interprétation non-intuitive.

### Comportement Correct (Après)
```python
# 'XYZ' (majuscules) = rotations extrinsèques
R.from_euler('XYZ', [theta_x, theta_y, theta_z], degrees=True)
```

**Effet** :
1. Rotation de `theta_x` autour de **X du labo** (fixe)
2. Rotation de `theta_y` autour de **Y du labo** (fixe)
3. Rotation de `theta_z` autour de **Z du labo** (fixe)

✅ **Avantage** : Les axes de référence restent fixes, l'interprétation est intuitive.

## Différence Mathématique

### Scipy Convention
- **Minuscules** (`'xyz'`) : Rotations **intrinsèques** (axes mobiles)
- **Majuscules** (`'XYZ'`) : Rotations **extrinsèques** (axes fixes)

### Équivalence
```
Intrinsèque 'xyz' ≡ Extrinsèque 'ZYX' (ordre inversé)
Extrinsèque 'XYZ' ≡ Intrinsèque 'zyx' (ordre inversé)
```

## Exemple Concret

### Rotation (45°, 30°, 0°)

#### Avec 'xyz' (intrinsèque - INCORRECT)
1. Tourner 45° autour de X du capteur
2. Tourner 30° autour de Y du capteur (qui a déjà tourné de 45° autour de X)
3. Pas de rotation autour de Z

**Résultat** : Orientation difficile à prédire intuitivement.

#### Avec 'XYZ' (extrinsèque - CORRECT)
1. Tourner 45° autour de X du labo (fixe)
2. Tourner 30° autour de Y du labo (fixe)
3. Pas de rotation autour de Z

**Résultat** : Orientation prévisible et intuitive.

## Impact sur le Code

### Fichiers Modifiés

1. **`cube_geometry.py`** (ligne 81)
   ```python
   # Avant
   return R.from_euler('xyz', [...], degrees=True)
   
   # Après
   return R.from_euler('XYZ', [...], degrees=True)
   ```

2. **`cube_geometry_quaternion.py`** (lignes 111, 126)
   ```python
   # quaternion_from_euler_xyz
   rot = R.from_euler('XYZ', [...], degrees=True)
   
   # euler_xyz_from_quaternion
   euler = rot.as_euler('XYZ', degrees=True)
   ```

### Tests à Mettre à Jour

Les tests doivent être mis à jour pour refléter le nouveau comportement :

```python
def test_extrinsic_rotation():
    """Vérifie que les rotations sont extrinsèques."""
    # Rotation de 90° autour de X (labo)
    rot = create_rotation_from_euler_xyz(90, 0, 0)
    
    # Appliquer à un vecteur Y du labo
    v_y = np.array([0, 1, 0])
    v_rotated = rot.apply(v_y)
    
    # Résultat attendu : Y -> Z (rotation autour de X fixe)
    expected = np.array([0, 0, 1])
    assert np.allclose(v_rotated, expected, atol=1e-10)
```

## Vérification Visuelle

### Test Simple
1. Mettre `theta_x = 90°`, `theta_y = 0°`, `theta_z = 0°`
2. Observer le cube dans la visualisation

**Attendu (extrinsèque)** :
- Le cube tourne de 90° autour de l'axe X du labo (rouge horizontal)
- Les faces colorées se réorientent de manière prévisible

**Avant (intrinsèque)** :
- Même résultat pour une seule rotation
- Mais pour des rotations composées, le comportement diffère

### Test Composé
1. Mettre `theta_x = 45°`, `theta_y = 45°`, `theta_z = 0°`

**Attendu (extrinsèque)** :
- D'abord 45° autour de X du labo
- Puis 45° autour de Y du labo (toujours fixe)
- Orientation finale prévisible

**Avant (intrinsèque)** :
- D'abord 45° autour de X du capteur
- Puis 45° autour de Y du capteur (qui a déjà tourné)
- Orientation finale moins intuitive

## Cohérence avec le Reste du Code

Cette correction assure la cohérence avec :
- **`adapter_mock_excitation_aware_acquisition.py`** : Les rotations du capteur sont appliquées dans le référentiel du labo
- **`sensor_transformation_panel.py`** : Les angles affichés correspondent aux axes fixes du labo
- **Visualisation** : Les axes `_labo` (fixes) sont la référence visuelle

## Conclusion

✅ **Correction appliquée** : `'xyz'` → `'XYZ'`  
✅ **Référentiel** : Axes fixes du laboratoire  
✅ **Intuitivité** : Rotations prévisibles et compréhensibles  
✅ **Cohérence** : Alignement avec le reste de l'application  

Cette correction est **critique** pour l'interprétation correcte des orientations du capteur.
