#!/usr/bin/env python3
"""
Module de rotation de référentiel pour projeter les mesures du capteur 3D 
du référentiel capteur vers le référentiel banc de test.

Basé sur la méthode quaternions pour une stabilité numérique optimale.
Adapté du script MATLAB rotationVectorFieldQuaternions.m

Auteur: Luis Saluden
Date: 2025-01-27
"""

import numpy as np
import math
from datetime import datetime
from typing import Tuple, Optional
try:
    from .AD9106_ADS131A04_DataBuffer_Module import AcquisitionSample
except ImportError:
    from AD9106_ADS131A04_DataBuffer_Module import AcquisitionSample


class FrameRotationProcessor:
    """
    Processeur de rotation de référentiel utilisant les quaternions.
    
    Permet de projeter les mesures du champ électrique 3D depuis le référentiel 
    du capteur vers le référentiel du banc de test via 3 rotations successives.
    """
    
    def __init__(self, theta_x: float = -45.0, theta_y: float = None, theta_z: float = 0.0):
        """
        Initialise le processeur avec les angles de rotation théoriques.
        
        Args:
            theta_x: Angle de rotation autour de l'axe X (degrés), défaut -45°
            theta_y: Angle de rotation autour de l'axe Y (degrés), défaut arctan(1/√2)
            theta_z: Angle de rotation autour de l'axe Z (degrés), défaut 0°
        """
        if theta_y is None:
            theta_y = math.degrees(math.atan(1 / math.sqrt(2)))
        
        self.theta_x = theta_x
        self.theta_y = theta_y 
        self.theta_z = theta_z
        
        # Calcul du quaternion de rotation composé
        self._update_rotation_quaternion()
        
        print(f"[DEBUG FrameRotation] Angles initialisés: θx={theta_x:.2f}°, θy={theta_y:.2f}°, θz={theta_z:.2f}°")
    
    def _update_rotation_quaternion(self):
        """Met à jour le quaternion de rotation composé à partir des angles."""
        # Conversion en radians
        theta_x_rad = math.radians(self.theta_x)
        theta_y_rad = math.radians(self.theta_y)
        theta_z_rad = math.radians(self.theta_z)
        
        # Création des quaternions élémentaires [w, x, y, z]
        # Convention: rotation positive selon règle main droite
        qx = np.array([math.cos(theta_x_rad/2), math.sin(theta_x_rad/2), 0, 0])
        qy = np.array([math.cos(theta_y_rad/2), 0, math.sin(theta_y_rad/2), 0])
        qz = np.array([math.cos(theta_z_rad/2), 0, 0, math.sin(theta_z_rad/2)])
        
        # Normalisation
        qx = qx / np.linalg.norm(qx)
        qy = qy / np.linalg.norm(qy)
        qz = qz / np.linalg.norm(qz)
        
        # Composition des rotations (ordre: Z, Y, X pour E_probe = Rz * Ry * Rx * E_bench)
        q_temp = self._quaternion_multiply(qz, qy)
        self.rotation_quaternion = self._quaternion_multiply(q_temp, qx)
        self.rotation_quaternion = self.rotation_quaternion / np.linalg.norm(self.rotation_quaternion)
        
        # Quaternion inverse pour rotation probe (sensor) → bench  
        # Si rotation_quaternion = Rz*Ry*Rx (bench→probe), alors inverse = (Rz*Ry*Rx)⁻¹ (probe→bench)
        self.inverse_quaternion = np.array([
            self.rotation_quaternion[0],  # w
            -self.rotation_quaternion[1], # -x
            -self.rotation_quaternion[2], # -y
            -self.rotation_quaternion[3]  # -z
        ])
    
    def set_rotation_angles(self, theta_x: float, theta_y: float, theta_z: float):
        """
        Met à jour les angles de rotation et recalcule le quaternion.
        
        Args:
            theta_x, theta_y, theta_z: Nouveaux angles en degrés
        """
        self.theta_x = theta_x
        self.theta_y = theta_y
        self.theta_z = theta_z
        self._update_rotation_quaternion()
        print(f"[DEBUG FrameRotation] Angles mis à jour: θx={theta_x:.2f}°, θy={theta_y:.2f}°, θz={theta_z:.2f}°")
    
    def rotate_sample(self, sample: AcquisitionSample, to_bench_frame: bool = True) -> AcquisitionSample:
        """
        Applique la rotation de référentiel à un échantillon d'acquisition.
        
        Convention : E_probe = Rz * Ry * Rx * E_bench
        
        Args:
            sample: Échantillon dans le référentiel source (probe/sensor)
            to_bench_frame: Si True, rotation probe→bench, sinon bench→probe
            
        Returns:
            Nouvel échantillon dans le référentiel cible
        """
        # Extraction des composantes du champ électrique 3D (in-phase ET quadrature)
        # === COMPOSANTES IN-PHASE ===
        ex_inphase_sensor = sample.adc1_ch1    # Ex in-phase
        ey_inphase_sensor = sample.adc1_ch3    # Ey in-phase  
        ez_inphase_sensor = sample.adc2_ch1    # Ez in-phase
        
        # === COMPOSANTES QUADRATURE ===
        ex_quadrature_sensor = sample.adc1_ch2 # Ex quadrature
        ey_quadrature_sensor = sample.adc1_ch4 # Ey quadrature
        ez_quadrature_sensor = sample.adc2_ch2 # Ez quadrature
        
        # Rotation des vecteurs champ électrique (même rotation pour in-phase et quadrature)
        ex_inphase_bench, ey_inphase_bench, ez_inphase_bench = self._rotate_vector(
            ex_inphase_sensor, ey_inphase_sensor, ez_inphase_sensor, to_bench_frame
        )
        
        ex_quadrature_bench, ey_quadrature_bench, ez_quadrature_bench = self._rotate_vector(
            ex_quadrature_sensor, ey_quadrature_sensor, ez_quadrature_sensor, to_bench_frame
        )
        
        # Création du nouvel échantillon avec TOUTES les composantes rotées
        rotated_sample = AcquisitionSample(
            timestamp=sample.timestamp,
            adc1_ch1=int(round(ex_inphase_bench)),     # Ex in-phase roté
            adc1_ch2=int(round(ex_quadrature_bench)),  # Ex quadrature roté
            adc1_ch3=int(round(ey_inphase_bench)),     # Ey in-phase roté
            adc1_ch4=int(round(ey_quadrature_bench)),  # Ey quadrature roté
            adc2_ch1=int(round(ez_inphase_bench)),     # Ez in-phase roté
            adc2_ch2=int(round(ez_quadrature_bench)),  # Ez quadrature roté
            adc2_ch3=sample.adc2_ch3,                  # Canal auxiliaire (inchangé)
            adc2_ch4=sample.adc2_ch4                   # Canal auxiliaire (inchangé)
        )
        
        return rotated_sample
    
    def _rotate_vector(self, x: float, y: float, z: float, to_bench_frame: bool = True) -> Tuple[float, float, float]:
        """
        Applique la rotation quaternion à un vecteur 3D.
        
        Args:
            x, y, z: Composantes du vecteur probe/sensor à faire tourner
            to_bench_frame: Si True, applique probe→bench (inverse), sinon bench→probe (direct)
            
        Returns:
            Tuple (x', y', z') du vecteur roté
        """
        vector = np.array([x, y, z])
        # to_bench_frame=True : probe→bench utilise l'inverse de (Rz*Ry*Rx)
        quaternion = self.inverse_quaternion if to_bench_frame else self.rotation_quaternion
        
        rotated_vector = self._quaternion_rotate(quaternion, vector)
        return rotated_vector[0], rotated_vector[1], rotated_vector[2]
    
    def _quaternion_multiply(self, q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
        """
        Multiplie deux quaternions q1 et q2.
        
        Args:
            q1, q2: Quaternions [w, x, y, z]
            
        Returns:
            Quaternion résultant de la multiplication
        """
        w1, x1, y1, z1 = q1
        w2, x2, y2, z2 = q2
        
        w = w1*w2 - x1*x2 - y1*y2 - z1*z2
        x = w1*x2 + x1*w2 + y1*z2 - z1*y2
        y = w1*y2 - x1*z2 + y1*w2 + z1*x2
        z = w1*z2 + x1*y2 - y1*x2 + z1*w2
        
        return np.array([w, x, y, z])
    
    def _quaternion_rotate(self, q: np.ndarray, v: np.ndarray) -> np.ndarray:
        """
        Applique une rotation quaternion à un vecteur 3D.
        
        Args:
            q: Quaternion de rotation [w, x, y, z]
            v: Vecteur 3D [x, y, z]
            
        Returns:
            Vecteur 3D roté [x', y', z']
        """
        # Conversion du vecteur en quaternion pur [0, x, y, z]
        v_quat = np.array([0, v[0], v[1], v[2]])
        
        # Calcul q * v_quat
        qv = self._quaternion_multiply(q, v_quat)
        
        # Quaternion conjugué de q
        q_conjugate = np.array([q[0], -q[1], -q[2], -q[3]])
        
        # Calcul q * v_quat * q_conjugate
        qv_rotated = self._quaternion_multiply(qv, q_conjugate)
        
        # Extraction de la partie vectorielle (ignorer la composante scalaire)
        return qv_rotated[1:4]
    
    def get_rotation_info(self) -> dict:
        """
        Retourne les informations sur la rotation actuelle.
        
        Returns:
            Dictionnaire avec angles et quaternion
        """
        return {
            'theta_x_deg': self.theta_x,
            'theta_y_deg': self.theta_y,
            'theta_z_deg': self.theta_z,
            'quaternion': self.rotation_quaternion.tolist(),
            'inverse_quaternion': self.inverse_quaternion.tolist()
        }


# Test du module si exécuté directement
if __name__ == "__main__":
    # Test basique du processeur de rotation
    processor = FrameRotationProcessor()
    
    # Création d'un échantillon test
    test_sample = AcquisitionSample(
        timestamp=datetime.now(),
        adc1_ch1=1000,  # Ex
        adc1_ch2=500,   # Ex quadrature
        adc1_ch3=2000,  # Ey
        adc1_ch4=600,   # Ey quadrature
        adc2_ch1=3000,  # Ez
        adc2_ch2=700,   # Ez quadrature
        adc2_ch3=100,   # Auxiliaire
        adc2_ch4=200    # Auxiliaire
    )
    
    print("Échantillon original (référentiel capteur):")
    print(f"Ex_I={test_sample.adc1_ch1}, Ex_Q={test_sample.adc1_ch2}")
    print(f"Ey_I={test_sample.adc1_ch3}, Ey_Q={test_sample.adc1_ch4}")  
    print(f"Ez_I={test_sample.adc2_ch1}, Ez_Q={test_sample.adc2_ch2}")
    
    # Rotation vers référentiel banc
    rotated_sample = processor.rotate_sample(test_sample, to_bench_frame=True)
    
    print("\nÉchantillon roté (référentiel banc):")
    print(f"Ex_I={rotated_sample.adc1_ch1}, Ex_Q={rotated_sample.adc1_ch2}")
    print(f"Ey_I={rotated_sample.adc1_ch3}, Ey_Q={rotated_sample.adc1_ch4}")
    print(f"Ez_I={rotated_sample.adc2_ch1}, Ez_Q={rotated_sample.adc2_ch2}")
    
    print("\nInfo rotation:")
    print(processor.get_rotation_info()) 