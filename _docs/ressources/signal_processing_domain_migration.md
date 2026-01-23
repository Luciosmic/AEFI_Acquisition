# Migration du Traitement du Signal vers le Domain

## Problème Identifié

### Invariants à Respecter
1. **Amplitude totale préservée**: `sqrt(I² + Q²)` doit rester constant après rotation de phase
2. **Signe de la composante in-phase préservé**: Si `I_original >= 0`, alors `I_rotated >= 0` (même amplitude). Si `I_original < 0`, alors `I_rotated < 0` (même amplitude)

### Problème Actuel

La rotation de phase dans `SignalPostProcessor` aligne toujours sur l'axe I positif, ce qui **perd le signe** quand `I_original` est négatif.

**Exemple:**
- Vecteur initial: `(I=-3.0, Q=4.0)`, amplitude = 5.0
- Après rotation standard: `(I=+5.0, Q=0.0)`
- **Problème**: Le signe est perdu! On devrait avoir `(I=-5.0, Q=0.0)`

**Code actuel (incorrect):**
```python
theta = math.atan2(q, i)
i_new = i * cos(theta) + q * sin(theta)  # Toujours positif
q_new = -i * sin(theta) + q * cos(theta)  # Devient 0
```

**Correction nécessaire:**
```python
theta = math.atan2(q, i)
i_temp = i * cos(theta) + q * sin(theta)  # Rotation standard (toujours positif)
mag = sqrt(i² + q²)
# Préserver le signe de I_original
i_new = mag if i >= 0 else -mag
q_new = 0.0
```

## Solution Proposée

### Migration vers le Domain

Déplacer la logique de traitement du signal dans `VoltageMeasurement` (domain layer) pour:
1. **Encapsuler les invariants** au niveau de l'objet de mesure
2. **Garantir la cohérence** des corrections
3. **Faciliter les tests** et la validation

### Structure Proposée

#### 1. Méthodes dans `VoltageMeasurement`

```python
@dataclass(frozen=True)
class VoltageMeasurement:
    # ... champs existants ...
    
    def apply_noise_correction(
        self, 
        noise_offset: 'VoltageMeasurement'
    ) -> 'VoltageMeasurement':
        """
        Soustrait l'offset de bruit.
        Préserve la structure (I, Q) - (I_offset, Q_offset).
        """
        return VoltageMeasurement(
            voltage_x_in_phase=self.voltage_x_in_phase - noise_offset.voltage_x_in_phase,
            voltage_x_quadrature=self.voltage_x_quadrature - noise_offset.voltage_x_quadrature,
            # ... autres axes ...
            timestamp=self.timestamp
        )
    
    def apply_phase_correction(
        self,
        phase_angle_rad: float,
        axis: str = 'x'  # 'x', 'y', 'z'
    ) -> 'VoltageMeasurement':
        """
        Applique la rotation de phase pour aligner sur l'axe I.
        
        INVARIANTS:
        - Amplitude préservée: sqrt(I² + Q²) reste constant
        - Signe préservé: sign(I_rotated) = sign(I_original)
        
        Args:
            phase_angle_rad: Angle de phase en radians (calculé avec atan2(Q, I))
            axis: Axe à corriger ('x', 'y', 'z')
        
        Returns:
            Nouveau VoltageMeasurement avec phase corrigée
        """
        # Rotation standard
        cos_t = math.cos(phase_angle_rad)
        sin_t = math.sin(phase_angle_rad)
        
        # Récupérer les valeurs pour l'axe spécifié
        i_val, q_val = self._get_axis_values(axis)
        
        # Rotation standard (alignement sur I positif)
        i_temp = i_val * cos_t + q_val * sin_t
        q_temp = -i_val * sin_t + q_val * cos_t
        
        # Calculer l'amplitude
        mag = math.sqrt(i_val**2 + q_val**2)
        
        # CORRECTION: Préserver le signe de I_original
        i_corrected = mag if i_val >= 0 else -mag
        q_corrected = 0.0
        
        # Retourner nouveau measurement avec valeurs corrigées
        return self._set_axis_values(axis, i_corrected, q_corrected)
    
    def apply_primary_field_correction(
        self,
        primary_offset: 'VoltageMeasurement'
    ) -> 'VoltageMeasurement':
        """
        Soustrait l'offset du champ primaire (tare).
        Préserve la structure après phase alignment (Q devrait être 0).
        """
        return VoltageMeasurement(
            voltage_x_in_phase=self.voltage_x_in_phase - primary_offset.voltage_x_in_phase,
            voltage_x_quadrature=self.voltage_x_quadrature - primary_offset.voltage_x_quadrature,
            # ... autres axes ...
            timestamp=self.timestamp
        )
    
    def get_complex_magnitude(self, axis: str = 'x') -> float:
        """Retourne l'amplitude complexe sqrt(I² + Q²) pour un axe."""
        i_val, q_val = self._get_axis_values(axis)
        return math.sqrt(i_val**2 + q_val**2)
    
    def _get_axis_values(self, axis: str) -> Tuple[float, float]:
        """Helper pour récupérer (I, Q) pour un axe."""
        if axis == 'x':
            return (self.voltage_x_in_phase, self.voltage_x_quadrature)
        elif axis == 'y':
            return (self.voltage_y_in_phase, self.voltage_y_quadrature)
        elif axis == 'z':
            return (self.voltage_z_in_phase, self.voltage_z_quadrature)
        else:
            raise ValueError(f"Invalid axis: {axis}")
    
    def _set_axis_values(self, axis: str, i: float, q: float) -> 'VoltageMeasurement':
        """Helper pour créer un nouveau measurement avec valeurs modifiées."""
        # ... implémentation ...
```

#### 2. Service de Calibration dans le Domain

```python
# domain/services/signal_calibration_service.py
class SignalCalibrationService:
    """
    Service pour calculer les paramètres de calibration.
    """
    
    @staticmethod
    def calculate_phase_angle(measurement: VoltageMeasurement, axis: str) -> float:
        """
        Calcule l'angle de phase pour aligner (I, Q) sur l'axe I.
        """
        i_val, q_val = measurement._get_axis_values(axis)
        return math.atan2(q_val, i_val)
```

#### 3. Migration de `SignalPostProcessor`

`SignalPostProcessor` devient un **adapter** qui utilise les méthodes du domain:

```python
class SignalPostProcessor:
    """
    Adapter pour l'interface: convertit Dict -> VoltageMeasurement,
    applique les corrections via les méthodes du domain,
    puis reconvertit en Dict.
    """
    
    def process_sample(self, raw_measurement: Dict[str, float]) -> Dict[str, float]:
        # 1. Convertir Dict -> VoltageMeasurement
        measurement = self._dict_to_measurement(raw_measurement)
        
        # 2. Appliquer corrections via méthodes du domain
        if self.state.noise_correction_enabled:
            noise_offset = self._get_noise_offset_measurement()
            measurement = measurement.apply_noise_correction(noise_offset)
        
        if self.state.phase_correction_enabled:
            for axis in ['x', 'y', 'z']:
                phase_angle = self.state.phase_angles.get(axis, 0.0)
                measurement = measurement.apply_phase_correction(phase_angle, axis)
        
        if self.state.primary_correction_enabled:
            primary_offset = self._get_primary_offset_measurement()
            measurement = measurement.apply_primary_field_correction(primary_offset)
        
        # 3. Convertir VoltageMeasurement -> Dict
        return self._measurement_to_dict(measurement)
```

## Plan de Migration

1. ✅ **Tests d'invariants** - Créer tests pour vérifier préservation amplitude et signe
2. ⏳ **Corriger la rotation de phase** - Implémenter préservation du signe
3. ⏳ **Ajouter méthodes dans VoltageMeasurement** - apply_noise_correction, apply_phase_correction, apply_primary_field_correction
4. ⏳ **Créer SignalCalibrationService** - Calcul des paramètres de calibration
5. ⏳ **Migrer SignalPostProcessor** - Utiliser les méthodes du domain
6. ⏳ **Mettre à jour les tests** - Vérifier que tout fonctionne
7. ⏳ **Mettre à jour ContinuousAcquisitionPresenter** - Utiliser la nouvelle logique

## Tests à Créer

1. ✅ `test_phase_rotation_preserves_amplitude` - Vérifie préservation amplitude
2. ✅ `test_phase_rotation_preserves_in_phase_sign` - Vérifie préservation signe (avec correction)
3. ⏳ `test_voltage_measurement_apply_phase_correction` - Test unitaire de la méthode
4. ⏳ `test_voltage_measurement_apply_noise_correction` - Test unitaire
5. ⏳ `test_voltage_measurement_apply_primary_correction` - Test unitaire
6. ⏳ `test_signal_post_processor_uses_domain_methods` - Test d'intégration
