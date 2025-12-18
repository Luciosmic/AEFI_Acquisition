import json
import os
from typing import Dict, Any

from domain.models.aefi_device.aggregates.aefi_device import AefiDevice
from domain.models.aefi_device.value_objects.quad_source_geometry import QuadSourceGeometry
from domain.models.aefi_device.value_objects.quaternion import Quaternion

class JsonDeviceRepository:
    """
    Infrastructure implementation of a repository to load AefiDevice from JSON.
    """
    
    def load(self, file_path: str) -> AefiDevice:
        """
        Loads a Device configuration from a JSON file.
        
        Expected JSON format:
        {
            "id": "AEFI-PROBE-001",
            "geometry": {
                "diagonal_spacing_mm": 50.0,
                "orientation_euler_deg": { "roll": 0.0, "pitch": 0.0, "yaw": 0.0 }
            }
        }
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Device config file not found: {file_path}")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        try:
            dev_id = data["id"]
            geo_data = data["geometry"]
            diag_mm = float(geo_data["diagonal_spacing_mm"])
            
            euler = geo_data.get("orientation_euler_deg", {"roll": 0, "pitch": 0, "yaw": 0})
            
            # Convert degrees to radians for Domain factory
            import math
            roll_rad = math.radians(euler.get("roll", 0.0))
            pitch_rad = math.radians(euler.get("pitch", 0.0))
            yaw_rad = math.radians(euler.get("yaw", 0.0))
            
            orientation = Quaternion.from_euler(roll_rad, pitch_rad, yaw_rad)
            
            geometry = QuadSourceGeometry(
                diagonal_spacing_mm=diag_mm,
                sensor_orientation=orientation
            )
            
            return AefiDevice(id=dev_id, geometry=geometry)
            
        except KeyError as e:
            raise ValueError(f"Invalid JSON format for AefiDevice: missing key {e}")
        except Exception as e:
             raise ValueError(f"Error loading AefiDevice: {e}")
