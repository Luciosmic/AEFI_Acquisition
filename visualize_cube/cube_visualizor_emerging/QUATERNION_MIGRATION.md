# Migration vers les Quaternions - Guide Technique

## Pourquoi les Quaternions ?

### Problèmes avec les Angles d'Euler

1. **Gimbal Lock** : Perte d'un degré de liberté quand deux axes s'alignent
   - Exemple : Si `theta_y = ±90°`, les rotations autour de X et Z deviennent équivalentes
   - Impossible de représenter certaines orientations

2. **Discontinuités** : Sauts brusques dans les angles
   - `(0°, 0°, 359°)` et `(0°, 0°, 1°)` sont presque identiques mais numériquement très différents

3. **Interpolation non-linéaire** : Interpoler entre deux orientations donne des résultats non-intuitifs
   - L'interpolation linéaire des angles ne donne PAS une rotation fluide

### Avantages des Quaternions

1. **Pas de Gimbal Lock** : Représentation continue de toutes les orientations
2. **Interpolation fluide** : SLERP (Spherical Linear Interpolation) pour des animations naturelles
3. **Composition efficace** : Multiplication de quaternions = composition de rotations
4. **Stabilité numérique** : Moins de problèmes d'arrondis
5. **Compact** : 4 nombres au lieu de 3 angles + ordre de rotation

## Architecture Proposée

### Modèle de Domaine (Quaternion-Based)

```python
@dataclass
class SensorOrientation:
    """Orientation du sensor représentée par un quaternion."""
    quaternion: np.ndarray  # [x, y, z, w] (scipy convention)
    
    @classmethod
    def default(cls):
        """Orientation par défaut du cube."""
        return cls(quaternion=get_default_quaternion())
    
    @classmethod
    def from_euler_xyz(cls, theta_x, theta_y, theta_z):
        """Crée depuis des angles d'Euler (pour compatibilité UI)."""
        quat = quaternion_from_euler_xyz(theta_x, theta_y, theta_z)
        return cls(quaternion=quat)
    
    def to_euler_xyz(self):
        """Convertit en angles d'Euler (pour affichage UI)."""
        return euler_xyz_from_quaternion(self.quaternion)
    
    def to_rotation(self):
        """Convertit en objet Rotation scipy."""
        return R.from_quat(self.quaternion)
```

### Flux de Données

```
UI (Euler Angles)
    ↓
quaternion_from_euler_xyz()
    ↓
SensorOrientation (Quaternion)
    ↓
to_rotation()
    ↓
PyVista Rendering
```

## Plan de Migration

### Étape 1 : Ajouter les fonctions quaternion (✅ FAIT)
- `cube_geometry_quaternion.py` créé avec toutes les fonctions

### Étape 2 : Modifier `SensorOrientation`
```python
# Avant (Euler)
@dataclass
class SensorOrientation:
    theta_x: float
    theta_y: float
    theta_z: float

# Après (Quaternion)
@dataclass
class SensorOrientation:
    quaternion: np.ndarray  # [x, y, z, w]
    
    def to_euler_xyz(self) -> tuple:
        """Pour affichage UI."""
        return euler_xyz_from_quaternion(self.quaternion)
```

### Étape 3 : Adapter le Presenter
```python
class CubeVisualizerPresenter:
    def _handle_update_angles_command(self, command: Command):
        # Convertir Euler -> Quaternion
        theta_x = command.data['theta_x']
        theta_y = command.data['theta_y']
        theta_z = command.data['theta_z']
        
        quat = quaternion_from_euler_xyz(theta_x, theta_y, theta_z)
        self.orientation.quaternion = quat
        
        self._publish_angles_changed_event()
    
    def _publish_angles_changed_event(self):
        # Convertir Quaternion -> Euler pour l'UI
        theta_x, theta_y, theta_z = self.orientation.to_euler_xyz()
        
        event = Event(
            event_type=EventType.ANGLES_CHANGED,
            data={'theta_x': theta_x, 'theta_y': theta_y, 'theta_z': theta_z}
        )
        self.event_bus.publish(event)
    
    def get_rotation(self):
        """Retourne l'objet Rotation scipy."""
        return R.from_quat(self.orientation.quaternion)
```

### Étape 4 : Adapter l'Adapter (PyVista)
```python
# Aucun changement nécessaire !
# L'adapter utilise déjà presenter.get_rotation()
# qui retourne un objet Rotation scipy
```

### Étape 5 : UI reste inchangée
```python
# L'UI continue d'utiliser des QDoubleSpinBox pour X, Y, Z
# La conversion Euler <-> Quaternion se fait dans le Presenter
```

## Fonctionnalités Bonus avec Quaternions

### 1. Interpolation Fluide (SLERP)
```python
def animate_rotation(q_start, q_end, duration_ms=1000, steps=60):
    """Anime une rotation de manière fluide."""
    for i in range(steps):
        t = i / (steps - 1)
        q_interpolated = quaternion_slerp(q_start, q_end, t)
        # Mettre à jour la visualisation
        yield q_interpolated
```

### 2. Composition de Rotations
```python
# Appliquer une rotation incrémentale
q_current = presenter.orientation.quaternion
q_delta = quaternion_from_euler_xyz(5, 0, 0)  # +5° autour de X
q_new = quaternion_multiply(q_current, q_delta)
```

### 3. Rotation Inverse
```python
# Quaternion conjugué = rotation inverse
def quaternion_inverse(q):
    return np.array([-q[0], -q[1], -q[2], q[3]])
```

## Tests de Non-Régression

### Test 1 : Équivalence Euler <-> Quaternion
```python
def test_euler_quaternion_roundtrip():
    theta_x, theta_y, theta_z = 45.0, 30.0, 60.0
    
    # Euler -> Quaternion -> Euler
    quat = quaternion_from_euler_xyz(theta_x, theta_y, theta_z)
    theta_x2, theta_y2, theta_z2 = euler_xyz_from_quaternion(quat)
    
    assert np.allclose([theta_x, theta_y, theta_z], 
                       [theta_x2, theta_y2, theta_z2], atol=1e-10)
```

### Test 2 : Gimbal Lock Résolu
```python
def test_no_gimbal_lock():
    # Configuration problématique avec Euler
    theta_x, theta_y, theta_z = 30.0, 90.0, 45.0
    
    quat = quaternion_from_euler_xyz(theta_x, theta_y, theta_z)
    rot = R.from_quat(quat)
    
    # Appliquer une petite rotation incrémentale
    v = np.array([1, 0, 0])
    v_rotated = rot.apply(v)
    
    # Vérifier que la rotation est bien appliquée
    assert not np.allclose(v, v_rotated)
```

### Test 3 : SLERP Interpolation
```python
def test_slerp_smoothness():
    q1 = quaternion_identity()
    q2 = quaternion_from_euler_xyz(90, 0, 0)
    
    # Interpoler à mi-chemin
    q_mid = quaternion_slerp(q1, q2, 0.5)
    theta_x, _, _ = euler_xyz_from_quaternion(q_mid)
    
    # Devrait être proche de 45°
    assert np.isclose(theta_x, 45.0, atol=1.0)
```

## Compatibilité Ascendante

L'UI continue d'utiliser des angles d'Euler pour la simplicité :
- Les utilisateurs voient toujours `X (deg)`, `Y (deg)`, `Z (deg)`
- La conversion Euler ↔ Quaternion est transparente
- Pas de changement visible pour l'utilisateur final

## Diagramme de Séquence (Mise à Jour)

```
User → UI: Change spin_x to 45°
UI → CommandBus: UpdateAnglesCommand(45, 30, 60)
CommandBus → Presenter: handle_update_angles
Presenter: quat = quaternion_from_euler_xyz(45, 30, 60)
Presenter: self.orientation.quaternion = quat
Presenter → EventBus: ANGLES_CHANGED(45, 30, 60)  # Reconverti en Euler
EventBus → Adapter: update_view()
Adapter → Presenter: get_rotation()  # Retourne R.from_quat(quat)
Adapter: Applique rotation au mesh PyVista
```

## Conclusion

**Avantages** :
- ✅ Stabilité numérique
- ✅ Pas de gimbal lock
- ✅ Interpolation fluide (SLERP)
- ✅ Composition efficace
- ✅ Compatibilité ascendante (UI inchangée)

**Inconvénients** :
- ⚠️ Moins intuitif pour les humains (mais transparent avec conversion)
- ⚠️ Légère surcharge de conversion Euler ↔ Quaternion (négligeable)

**Recommandation** : **Migration fortement recommandée** pour un code robuste et évolutif.
