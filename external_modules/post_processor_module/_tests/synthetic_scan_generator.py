"""
SyntheticScanGenerator - Generates deterministic test data for analytic validation.
Produces scan data with known characteristics (phase, amplitude, rotation) for testing.
"""

from typing import Tuple, Optional, Dict
import numpy as np
import pandas as pd
from scipy.spatial.transform import Rotation as R


class SyntheticScanGenerator:
    """
    Generates synthetic scan data using analytic functions.
    Output formats:
    - NumPy array: (N, N, 6) for internal testing
    - DataFrame: for pipeline preprocessing testing
    """
    
    def __init__(self, grid_size: int = 50, scan_range: float = 10.0):
        """
        Initialize generator.
        
        Args:
            grid_size: Number of points per axis (for square grid)
            scan_range: Physical dimensions of scan (e.g., 10mm)
        """
        self.grid_size = grid_size
        self.scan_range = scan_range
        self.x = np.linspace(-scan_range/2, scan_range/2, grid_size)
        self.y = np.linspace(-scan_range/2, scan_range/2, grid_size)
        self.X, self.Y = np.meshgrid(self.x, self.y)
        
    def generate_base_signal(self) -> np.ndarray:
        """
        Generate a base vector field for testing.
        Field: Simple non-uniform field to verify transformations.
        Ux = sin(kx * x) * cos(ky * y)
        Uy = cos(kx * x) * sin(ky * y)
        Uz = sin(kx * x) * sin(ky * y)
        
        Returns:
            Vector field [Ux_I, Ux_Q, Uy_I, Uy_Q, Uz_I, Uz_Q], shape (N, N, 6)
            Initially, Quadrature component is 0.
        """
        kx = 2 * np.pi / (2 * self.scan_range)  # half cycle over range
        ky = 2 * np.pi / (2 * self.scan_range)
        
        # In-Phase components (Real part)
        Ux_I = np.sin(kx * self.X) * np.cos(ky * self.Y)
        Uy_I = np.cos(kx * self.X) * np.sin(ky * self.Y)
        Uz_I = np.sin(kx * self.X) * np.sin(ky * self.Y)
        
        # Quadrature components (Imaginary part) - initially 0
        Ux_Q = np.zeros_like(self.X)
        Uy_Q = np.zeros_like(self.Y)
        Uz_Q = np.zeros_like(self.X) # Corrected from self.Z (which doesn't exist)
        
        # Stack into (N, N, 6)
        data = np.stack([Ux_I, Ux_Q, Uy_I, Uy_Q, Uz_I, Uz_Q], axis=-1)
        return data

    def add_phase_offset(self, data: np.ndarray, phase_angles: Tuple[float, float, float]) -> np.ndarray:
        """
        Add constant phase offset to each axis.
        Effectively rotates the complex vector (I + jQ) by phase angle phi.
        V_new = V_old * exp(j * phi)
        
        Args:
            data: Input data (N, N, 6)
            phase_angles: (phi_x, phi_y, phi_z) in radians
            
        Returns:
            Data with phase offset applied
        """
        data_out = data.copy()
        angle_x, angle_y, angle_z = phase_angles
        
        angles = [angle_x, angle_y, angle_z]
        axis_indices = [(0, 1), (2, 3), (4, 5)] # (I, Q) indices for X, Y, Z
        
        for (i_idx, q_idx), phi in zip(axis_indices, angles):
            I = data[:, :, i_idx]
            Q = data[:, :, q_idx]
            
            # Apply rotation
            # I' = I cos(phi) - Q sin(phi)
            # Q' = I sin(phi) + Q cos(phi)
            
            I_new = I * np.cos(phi) - Q * np.sin(phi)
            Q_new = I * np.sin(phi) + Q * np.cos(phi)
            
            data_out[:, :, i_idx] = I_new
            data_out[:, :, q_idx] = Q_new
            
        return data_out

    def add_dc_offset(self, data: np.ndarray, offsets: np.ndarray) -> np.ndarray:
        """
        Add DC offset (Primary Field Amplitude) to each channel.
        
        Args:
            data: Input data (N, N, 6)
            offsets: Array of 6 offsets [Off_Ux_I, Off_Ux_Q, ...]
            
        Returns:
            Data with DC offset added
        """
        if len(offsets) != 6:
            raise ValueError("Offsets must have 6 components")
            
        data_out = data.copy()
        # Broadcast offsets to (N, N, 6)
        data_out += offsets[np.newaxis, np.newaxis, :]
        
        return data_out
        
    def rotate_frame(self, data: np.ndarray, rotation_angles: Tuple[float, float, float]) -> np.ndarray:
        """
        Apply 3D spatial rotation to the vector field (inverse of sensor rotation).
        If we want to simulate a sensor rotated by angles, the measured field 
        is R_inv * Field_Laboratory. 
        Wait, usually: V_sensor = R_sensor_to_lab * V_lab? No.
        If sensor is rotated by R, a vector V in lab frame is seen as V' = R^(-1) * V in sensor frame.
        Here we just want to apply a known rotation to verify the rotator.
        
        Args:
            data: Input data (N, N, 6)
            rotation_angles: (theta_x, theta_y, theta_z) in degrees
        
        Returns:
            Rotated vector field
        """
        # Using the existing rotator logic to apply "forward" rotation
        # We can implement it manually here to be independent
        
        rot = R.from_euler('XYZ', rotation_angles, degrees=True)
        
        data_out = data.copy()
        
        # Reshape to (M, 6)
        flat = data.reshape(-1, 6)
        
        # Vectors (Real parts and Imag parts separate)
        vec_I = flat[:, [0, 2, 4]]
        vec_Q = flat[:, [1, 3, 5]]
        
        # Rotate
        vec_I_rot = rot.apply(vec_I)
        vec_Q_rot = rot.apply(vec_Q)
        
        flat_out = np.zeros_like(flat)
        flat_out[:, [0, 2, 4]] = vec_I_rot
        flat_out[:, [1, 3, 5]] = vec_Q_rot
        
        return flat_out.reshape(data.shape)

    def to_dataframe(self, data: np.ndarray) -> pd.DataFrame:
        """
        Convert (N, N, 6) array to DataFrame with columns:
        x, y, voltage_x_in_phase, voltage_x_quadrature, ...
        """
        rows = []
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                x_val = self.x[j] # x varies with column index
                y_val = self.y[i] # y varies with row index (image convention, y grows down? or up? standardized on meshgrid)
                # self.X[i, j] is x_val, self.Y[i, j] is y_val
                
                vals = data[i, j, :]
                row = {
                    'x': self.X[i, j],
                    'y': self.Y[i, j],
                    'voltage_x_in_phase': vals[0],
                    'voltage_x_quadrature': vals[1],
                    'voltage_y_in_phase': vals[2],
                    'voltage_y_quadrature': vals[3],
                    'voltage_z_in_phase': vals[4],
                    'voltage_z_quadrature': vals[5],
                }
                rows.append(row)
        return pd.DataFrame(rows)

