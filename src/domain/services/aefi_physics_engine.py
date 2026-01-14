from typing import Dict
from ..model.aggregates.aefi_device import AefiDevice
from ..model.value_objects.vector_3d import Vector3D

class AefiPhysicsEngine:
    """
    Domain Service encapsulating the physical laws governing the AEFI device.
    Pure logic, no state.
    """
    
    # Coulomb constant approximation or specific calibration factor 'k'
    # E = k * V / d^2 (Simplified model as per prompt)
    K_FACTOR = 1.0 

    def compute_total_field(self, device: AefiDevice, voltages: Dict[str, float]) -> Vector3D:
        """
        Computes the total Electric Field vector sum at the sensor position.
        
        Args:
            device: The AefiDevice configuration.
            voltages: A dictionary mapping source_id (e.g., 'S1') to voltage (float).
            
        Returns:
            Vector3D: The resulting total field vector in the GLOBAL frame of the Device.
        """
        total_field = Vector3D(0.0, 0.0, 0.0)
        
        interactions = device.get_interactions()
        
        for pair in interactions:
            if pair.source_id not in voltages:
                continue
                
            v = voltages[pair.source_id]
            d_vec = pair.relative_vector
            dist = d_vec.magnitude
            
            if dist == 0:
                continue # Avoid division by zero
                
            # E_magnitude = k * V / d^2
            # Direction is along the unit vector from source to sensor (d_vec.normalize())
            # Assuming positive voltage repels/attracts (sign convention matters, here assuming standard)
            
            e_mag = (self.K_FACTOR * v) / (dist ** 2)
            
            e_vec = d_vec.normalize().scale(e_mag)
            
            total_field = total_field + e_vec
            
        # The prompt specifies: 
        # "Crucial: Applique la rotation inverse du capteur" 
        # BUT also says: "partons du principe qu'on veut le champ dans le repère global du Device."
        # If we want the field in the global device frame, and the sources are already defined in the device frame,
        # then the formatting is correct as is.
        #
        # However, the sensor itself might have an orientation *relative* to the device frame.
        # If the sensor is rotated, its local X/Y/Z axes differ from the Device X/Y/Z.
        # Usually, a sensor measures in its OWN local frame. 
        # The prompt implies: "Applique la rotation inverse... pour exprimer le champ dans le repère du capteur".
        # Let's support the sensor frame output as it's more physically useful for reading values.
        
        # We will assume constraints say "Global Device Frame" for this code as per prompt end-note:
        # "Pour ce code, partons du principe qu'on veut le champ dans le repère global du Device."
        
        # So we simply return total_field as computed (which is in Device Frame).
        # We DO NOT apply rotation if we want it in Device Frame.
        
        return total_field
