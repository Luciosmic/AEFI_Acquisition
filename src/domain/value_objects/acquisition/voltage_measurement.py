"""
Domain: Acquisition - Voltage Measurement

Responsibility:
    Represents a single voltage measurement from the electric field sensor.
    Uses ubiquitous language (domain terminology) instead of hardware channels.

Rationale:
    Encapsulates the 6 voltage components (X, Y, Z in-phase and quadrature)
    measured by the ADC. Immutable value object with timestamp.

Design:
    - Frozen dataclass (immutable)
    - Domain language: voltage_x_in_phase instead of adc1_ch1
    - Mapping to hardware done in infrastructure layer
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Tuple
import math

@dataclass(frozen=True)
class VoltageMeasurement:
    """Voltage measurement from electric field sensor.
    
    Represents the 6 components of the electric field measurement:
    - X, Y, Z directions
    - In-phase and quadrature components for each direction
    
    Mapping to ADC channels (done in infrastructure):
    - voltage_x_in_phase = ADC1_Ch1
    - voltage_x_quadrature = ADC1_Ch2
    - voltage_y_in_phase = ADC1_Ch3
    - voltage_y_quadrature = ADC1_Ch4
    - voltage_z_in_phase = ADC2_Ch1
    - voltage_z_quadrature = ADC2_Ch2
    """
    
    # X direction
    voltage_x_in_phase: float  # Volts
    voltage_x_quadrature: float  # Volts
    
    # Y direction
    voltage_y_in_phase: float  # Volts
    voltage_y_quadrature: float  # Volts
    
    # Z direction
    voltage_z_in_phase: float  # Volts
    voltage_z_quadrature: float  # Volts
    
    # Metadata
    timestamp: datetime
    
    # Quality metric (optional)
    uncertainty_estimate_volts: Optional[float] = None  # Estimated measurement uncertainty (±V)
    
    # Statistical Metadata (optional, for averaged measurements)
    std_dev_x_in_phase: Optional[float] = None
    std_dev_x_quadrature: Optional[float] = None
    std_dev_y_in_phase: Optional[float] = None
    std_dev_y_quadrature: Optional[float] = None
    std_dev_z_in_phase: Optional[float] = None
    std_dev_z_quadrature: Optional[float] = None
    
    def __post_init__(self):
        """Validate voltage values are finite."""
        for field_name in ['voltage_x_in_phase', 'voltage_x_quadrature',
                          'voltage_y_in_phase', 'voltage_y_quadrature',
                          'voltage_z_in_phase', 'voltage_z_quadrature']:
            value = getattr(self, field_name)
            if not math.isfinite(value):
                raise ValueError(f"{field_name} must be finite, got {value}")
    
    def apply_noise_correction(self, noise_offset: 'VoltageMeasurement') -> 'VoltageMeasurement':
        """
        Soustrait l'offset de bruit pour chaque axe.
        Préserve la structure (I, Q) - (I_offset, Q_offset).
        
        Args:
            noise_offset: VoltageMeasurement contenant les offsets de bruit
        
        Returns:
            Nouveau VoltageMeasurement avec bruit soustrait
        """
        return VoltageMeasurement(
            voltage_x_in_phase=self.voltage_x_in_phase - noise_offset.voltage_x_in_phase,
            voltage_x_quadrature=self.voltage_x_quadrature - noise_offset.voltage_x_quadrature,
            voltage_y_in_phase=self.voltage_y_in_phase - noise_offset.voltage_y_in_phase,
            voltage_y_quadrature=self.voltage_y_quadrature - noise_offset.voltage_y_quadrature,
            voltage_z_in_phase=self.voltage_z_in_phase - noise_offset.voltage_z_in_phase,
            voltage_z_quadrature=self.voltage_z_quadrature - noise_offset.voltage_z_quadrature,
            timestamp=self.timestamp,
            uncertainty_estimate_volts=self.uncertainty_estimate_volts,
            std_dev_x_in_phase=self.std_dev_x_in_phase,
            std_dev_x_quadrature=self.std_dev_x_quadrature,
            std_dev_y_in_phase=self.std_dev_y_in_phase,
            std_dev_y_quadrature=self.std_dev_y_quadrature,
            std_dev_z_in_phase=self.std_dev_z_in_phase,
            std_dev_z_quadrature=self.std_dev_z_quadrature,
        )
    
    def apply_phase_correction(self, phase_angles: Dict[str, float]) -> 'VoltageMeasurement':
        """
        Applique la rotation de phase pour aligner sur l'axe I.
        
        INVARIANTS:
        - Amplitude préservée: sqrt(I² + Q²) reste constant
        - Signe préservé: sign(I_rotated) = sign(I_original)
        
        Args:
            phase_angles: Dict avec clés 'x', 'y', 'z' et valeurs en radians
        
        Returns:
            Nouveau VoltageMeasurement avec phase corrigée
        """
        result = self
        
        for axis in ['x', 'y', 'z']:
            if axis in phase_angles:
                theta = phase_angles[axis]
                result = result._apply_phase_correction_to_axis(axis, theta)
        
        return result
    
    def apply_primary_field_correction(self, primary_offset: 'VoltageMeasurement') -> 'VoltageMeasurement':
        """
        Soustrait l'offset du champ primaire (tare).
        Préserve la structure après phase alignment (Q devrait être 0).
        
        Args:
            primary_offset: VoltageMeasurement contenant les offsets primaires
        
        Returns:
            Nouveau VoltageMeasurement avec offset primaire soustrait
        """
        return VoltageMeasurement(
            voltage_x_in_phase=self.voltage_x_in_phase - primary_offset.voltage_x_in_phase,
            voltage_x_quadrature=self.voltage_x_quadrature - primary_offset.voltage_x_quadrature,
            voltage_y_in_phase=self.voltage_y_in_phase - primary_offset.voltage_y_in_phase,
            voltage_y_quadrature=self.voltage_y_quadrature - primary_offset.voltage_y_quadrature,
            voltage_z_in_phase=self.voltage_z_in_phase - primary_offset.voltage_z_in_phase,
            voltage_z_quadrature=self.voltage_z_quadrature - primary_offset.voltage_z_quadrature,
            timestamp=self.timestamp,
            uncertainty_estimate_volts=self.uncertainty_estimate_volts,
            std_dev_x_in_phase=self.std_dev_x_in_phase,
            std_dev_x_quadrature=self.std_dev_x_quadrature,
            std_dev_y_in_phase=self.std_dev_y_in_phase,
            std_dev_y_quadrature=self.std_dev_y_quadrature,
            std_dev_z_in_phase=self.std_dev_z_in_phase,
            std_dev_z_quadrature=self.std_dev_z_quadrature,
        )
    
    def get_complex_magnitude(self, axis: str) -> float:
        """
        Retourne l'amplitude complexe sqrt(I² + Q²) pour un axe donné.
        
        Args:
            axis: 'x', 'y', ou 'z'
        
        Returns:
            Amplitude complexe en volts
        """
        i_val, q_val = self._get_axis_values(axis)
        return math.sqrt(i_val**2 + q_val**2)
    
    def _get_axis_values(self, axis: str) -> Tuple[float, float]:
        """
        Helper privé pour récupérer (I, Q) pour un axe.
        
        Args:
            axis: 'x', 'y', ou 'z'
        
        Returns:
            Tuple (I, Q) en volts
        """
        if axis == 'x':
            return (self.voltage_x_in_phase, self.voltage_x_quadrature)
        elif axis == 'y':
            return (self.voltage_y_in_phase, self.voltage_y_quadrature)
        elif axis == 'z':
            return (self.voltage_z_in_phase, self.voltage_z_quadrature)
        else:
            raise ValueError(f"Invalid axis: {axis}. Must be 'x', 'y', or 'z'")
    
    def _set_axis_values(self, axis: str, i: float, q: float) -> 'VoltageMeasurement':
        """
        Helper privé pour créer un nouveau measurement avec valeurs modifiées pour un axe.
        
        Args:
            axis: 'x', 'y', ou 'z'
            i: Nouvelle valeur in-phase
            q: Nouvelle valeur quadrature
        
        Returns:
            Nouveau VoltageMeasurement avec valeurs modifiées
        """
        if axis == 'x':
            return VoltageMeasurement(
                voltage_x_in_phase=i,
                voltage_x_quadrature=q,
                voltage_y_in_phase=self.voltage_y_in_phase,
                voltage_y_quadrature=self.voltage_y_quadrature,
                voltage_z_in_phase=self.voltage_z_in_phase,
                voltage_z_quadrature=self.voltage_z_quadrature,
                timestamp=self.timestamp,
                uncertainty_estimate_volts=self.uncertainty_estimate_volts,
                std_dev_x_in_phase=self.std_dev_x_in_phase,
                std_dev_x_quadrature=self.std_dev_x_quadrature,
                std_dev_y_in_phase=self.std_dev_y_in_phase,
                std_dev_y_quadrature=self.std_dev_y_quadrature,
                std_dev_z_in_phase=self.std_dev_z_in_phase,
                std_dev_z_quadrature=self.std_dev_z_quadrature,
            )
        elif axis == 'y':
            return VoltageMeasurement(
                voltage_x_in_phase=self.voltage_x_in_phase,
                voltage_x_quadrature=self.voltage_x_quadrature,
                voltage_y_in_phase=i,
                voltage_y_quadrature=q,
                voltage_z_in_phase=self.voltage_z_in_phase,
                voltage_z_quadrature=self.voltage_z_quadrature,
                timestamp=self.timestamp,
                uncertainty_estimate_volts=self.uncertainty_estimate_volts,
                std_dev_x_in_phase=self.std_dev_x_in_phase,
                std_dev_x_quadrature=self.std_dev_x_quadrature,
                std_dev_y_in_phase=self.std_dev_y_in_phase,
                std_dev_y_quadrature=self.std_dev_y_quadrature,
                std_dev_z_in_phase=self.std_dev_z_in_phase,
                std_dev_z_quadrature=self.std_dev_z_quadrature,
            )
        elif axis == 'z':
            return VoltageMeasurement(
                voltage_x_in_phase=self.voltage_x_in_phase,
                voltage_x_quadrature=self.voltage_x_quadrature,
                voltage_y_in_phase=self.voltage_y_in_phase,
                voltage_y_quadrature=self.voltage_y_quadrature,
                voltage_z_in_phase=i,
                voltage_z_quadrature=q,
                timestamp=self.timestamp,
                uncertainty_estimate_volts=self.uncertainty_estimate_volts,
                std_dev_x_in_phase=self.std_dev_x_in_phase,
                std_dev_x_quadrature=self.std_dev_x_quadrature,
                std_dev_y_in_phase=self.std_dev_y_in_phase,
                std_dev_y_quadrature=self.std_dev_y_quadrature,
                std_dev_z_in_phase=self.std_dev_z_in_phase,
                std_dev_z_quadrature=self.std_dev_z_quadrature,
            )
        else:
            raise ValueError(f"Invalid axis: {axis}. Must be 'x', 'y', or 'z'")
    
    def _apply_phase_correction_to_axis(self, axis: str, theta: float) -> 'VoltageMeasurement':
        """
        Applique la rotation de phase pour un axe spécifique.
        
        CORRECTION: Préserve le signe de I_original après rotation.
        
        Args:
            axis: 'x', 'y', ou 'z'
            theta: Angle de phase en radians
        
        Returns:
            Nouveau VoltageMeasurement avec phase corrigée pour cet axe
        """
        i_val, q_val = self._get_axis_values(axis)
        
        # Rotation standard (alignement sur I positif)
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        i_temp = i_val * cos_t + q_val * sin_t
        
        # Calculer l'amplitude
        mag = math.sqrt(i_val**2 + q_val**2)
        
        # CORRECTION: Préserver le signe de I_original
        i_corrected = mag if i_val >= 0 else -mag
        q_corrected = 0.0
        
        return self._set_axis_values(axis, i_corrected, q_corrected)

