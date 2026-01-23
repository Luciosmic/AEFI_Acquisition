"""
Infrastructure: JSON Voltage Measurement Reference Repository

Responsibility:
    Persist VoltageMeasurementReference to JSON files in .aefi_acquisition/calibrations/voltage_reference_measurement/

Rationale:
    - Simple, human-readable format
    - Easy to version control
    - Sufficient for calibration data persistence

Design:
    - Implements IVoltageMeasurementReferenceRepository
    - Uses JSON for serialization
    - Stores files in .aefi_acquisition/calibrations/voltage_reference_measurement/
"""
import json
import os
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from domain.repositories.i_voltage_measurement_reference_repository import IVoltageMeasurementReferenceRepository
from domain.value_objects.acquisition.voltage_measurement_reference import VoltageMeasurementReference
from domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement
from domain.value_objects.geometric.position_2d import Position2D
from domain.value_objects.excitation.excitation_parameters import ExcitationParameters
from domain.value_objects.excitation.excitation_mode import ExcitationMode
from domain.value_objects.excitation.excitation_level import ExcitationLevel


class JsonVoltageMeasurementReferenceRepository(IVoltageMeasurementReferenceRepository):
    """
    JSON implementation of VoltageMeasurementReference repository.
    
    Stores references as JSON files in .aefi_acquisition/calibrations/voltage_reference_measurement/
    """
    
    def __init__(self, base_config_dir: Optional[str] = None):
        """
        Initialize repository.
        
        Args:
            base_config_dir: Base configuration directory. If None, uses .aefi_acquisition in project root.
        """
        if base_config_dir:
            self.base_dir = Path(base_config_dir)
        else:
            # Default to .aefi_configuration in project root (one level up from src)
            # Path structure: project_root/src/infrastructure/persistence/file.py
            project_root = Path(__file__).parent.parent.parent.parent
            self.base_dir = project_root / ".aefi_acquisition"
        
        self.calibrations_dir = self.base_dir / "calibrations" / "voltage_reference_measurement"
        self.calibrations_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_file_path(self, name: str) -> Path:
        """Get file path for a reference name."""
        safe_name = "".join([c for c in name if c.isalnum() or c in ('-', '_', '.')])
        return self.calibrations_dir / f"{safe_name}.json"
    
    def _generate_name_from_timestamp(self, timestamp: datetime) -> str:
        """Generate a name from timestamp."""
        return timestamp.strftime("%Y-%m-%d_%H%M%S")
    
    def _serialize_voltage_measurement(self, measurement: Optional[VoltageMeasurement]) -> Optional[dict]:
        """Serialize VoltageMeasurement to dict."""
        if measurement is None:
            return None
        
        return {
            "voltage_x_in_phase": measurement.voltage_x_in_phase,
            "voltage_x_quadrature": measurement.voltage_x_quadrature,
            "voltage_y_in_phase": measurement.voltage_y_in_phase,
            "voltage_y_quadrature": measurement.voltage_y_quadrature,
            "voltage_z_in_phase": measurement.voltage_z_in_phase,
            "voltage_z_quadrature": measurement.voltage_z_quadrature,
            "timestamp": measurement.timestamp.isoformat(),
        }
    
    def _deserialize_voltage_measurement(self, data: Optional[dict]) -> Optional[VoltageMeasurement]:
        """Deserialize dict to VoltageMeasurement."""
        if data is None:
            return None
        
        return VoltageMeasurement(
            voltage_x_in_phase=data["voltage_x_in_phase"],
            voltage_x_quadrature=data["voltage_x_quadrature"],
            voltage_y_in_phase=data["voltage_y_in_phase"],
            voltage_y_quadrature=data["voltage_y_quadrature"],
            voltage_z_in_phase=data["voltage_z_in_phase"],
            voltage_z_quadrature=data["voltage_z_quadrature"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )
    
    def _serialize_position(self, position: Optional[Position2D]) -> Optional[dict]:
        """Serialize Position2D to dict."""
        if position is None:
            return None
        
        return {"x": position.x, "y": position.y}
    
    def _deserialize_position(self, data: Optional[dict]) -> Optional[Position2D]:
        """Deserialize dict to Position2D."""
        if data is None:
            return None
        
        return Position2D(x=data["x"], y=data["y"])
    
    def _serialize_excitation(self, excitation: Optional[ExcitationParameters]) -> Optional[dict]:
        """Serialize ExcitationParameters to dict."""
        if excitation is None:
            return None
        
        return {
            "mode": excitation.mode.name,
            "level": excitation.level.value,
            "frequency": excitation.frequency,
        }
    
    def _deserialize_excitation(self, data: Optional[dict]) -> Optional[ExcitationParameters]:
        """Deserialize dict to ExcitationParameters."""
        if data is None:
            return None
        
        mode = ExcitationMode[data["mode"]]
        level = ExcitationLevel(data["level"])
        frequency = data["frequency"]
        
        return ExcitationParameters(mode=mode, level=level, frequency=frequency)
    
    def _serialize_reference(self, reference: VoltageMeasurementReference) -> dict:
        """Serialize VoltageMeasurementReference to dict."""
        return {
            "noise_offset": self._serialize_voltage_measurement(reference.noise_offset),
            "phase_angles": reference.phase_angles.copy(),
            "primary_offset": self._serialize_voltage_measurement(reference.primary_offset),
            "calibration_timestamp": reference.calibration_timestamp.isoformat(),
            "calibration_author": reference.calibration_author,
            "calibration_position": self._serialize_position(reference.calibration_position),
            "excitation_parameters": self._serialize_excitation(reference.excitation_parameters),
        }
    
    def _deserialize_reference(self, data: dict) -> VoltageMeasurementReference:
        """Deserialize dict to VoltageMeasurementReference."""
        return VoltageMeasurementReference(
            noise_offset=self._deserialize_voltage_measurement(data.get("noise_offset")),
            phase_angles=data.get("phase_angles", {}).copy(),
            primary_offset=self._deserialize_voltage_measurement(data.get("primary_offset")),
            calibration_timestamp=datetime.fromisoformat(data["calibration_timestamp"]),
            calibration_author=data.get("calibration_author"),
            calibration_position=self._deserialize_position(data.get("calibration_position")),
            excitation_parameters=self._deserialize_excitation(data.get("excitation_parameters")),
        )
    
    def save(self, reference: VoltageMeasurementReference, name: Optional[str] = None) -> str:
        """
        Persist a voltage measurement reference.
        
        Args:
            reference: VoltageMeasurementReference to save
            name: Optional name/identifier. If None, generates from timestamp.
        
        Returns:
            Name/identifier of the saved reference
        """
        if name is None:
            name = self._generate_name_from_timestamp(reference.calibration_timestamp)
        
        file_path = self._get_file_path(name)
        
        data = self._serialize_reference(reference)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return name
    
    def load(self, name: str) -> Optional[VoltageMeasurementReference]:
        """
        Load a voltage measurement reference by name.
        
        Args:
            name: Identifier/name of the reference to load
        
        Returns:
            VoltageMeasurementReference if found, None otherwise
        """
        file_path = self._get_file_path(name)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return self._deserialize_reference(data)
        except Exception as e:
            # Log error and return None
            print(f"[JsonVoltageMeasurementReferenceRepository] Error loading {name}: {e}")
            return None
    
    def load_latest(self) -> Optional[VoltageMeasurementReference]:
        """
        Load the most recent voltage measurement reference.
        
        Returns:
            Most recent VoltageMeasurementReference if any exist, None otherwise
        """
        all_names = self.list_all()
        if not all_names:
            return None
        
        # Sort by name (which includes timestamp) and get latest
        all_names.sort(reverse=True)
        return self.load(all_names[0])
    
    def list_all(self) -> List[str]:
        """
        List all available reference names/identifiers.
        
        Returns:
            List of reference names (without .json extension)
        """
        if not self.calibrations_dir.exists():
            return []
        
        names = []
        for file_path in self.calibrations_dir.glob("*.json"):
            # Remove .json extension
            name = file_path.stem
            names.append(name)
        
        return sorted(names)
    
    def delete(self, name: str) -> bool:
        """
        Delete a voltage measurement reference by name.
        
        Args:
            name: Identifier/name of the reference to delete
        
        Returns:
            True if deleted, False if not found
        """
        file_path = self._get_file_path(name)
        
        if not file_path.exists():
            return False
        
        try:
            file_path.unlink()
            return True
        except Exception as e:
            print(f"[JsonVoltageMeasurementReferenceRepository] Error deleting {name}: {e}")
            return False
