#!/usr/bin/env python3
"""
Module unifié de post-processing pour les données de champ électrique.

Regroupe toutes les transformations de post-traitement :
- Rotation de référentiel (sensor → bench)
- Compensation des signaux parasites (offset)
- Correction de phase (détection synchrone)

Auteur: Luis Saluden
Date: 2025-01-27
"""

import numpy as np
from typing import Dict, Tuple, Optional, List, Any
from dataclasses import dataclass, field
import math
from datetime import datetime
import os
import pickle
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
        

from scipy.optimize import minimize_scalar
        

# Import des types de données
from AD9106_ADS131A04_ElectricField_3D.components.AD9106_ADS131A04_DataBuffer_Module import AdaptiveDataBuffer, AcquisitionSample
        

@dataclass
class PostProcessingConfig:
    """Configuration simplifiée du post-processing"""

    # Stockage des valeurs de compensation
    compensation_storage: Dict[str, Dict] = field(default_factory=lambda: {
        'offset_exc_off': {
            'Ex_real': 0.0,
            'Ex_imag': 0.0,
            'Ey_real': 0.0,
            'Ey_imag': 0.0,
            'Ez_real': 0.0,
            'Ez_imag': 0.0
        },      # Valeurs d'offset sans excitation
        'offset_exc_on': {
            'Ex_real': 0.0,
            'Ex_imag': 0.0,
            'Ey_real': 0.0,
            'Ey_imag': 0.0,
            'Ez_real': 0.0,
            'Ez_imag': 0.0
        },       # Valeurs d'offset avec excitation
        'phase_corrections': {     # Corrections de phase
            'Ex_origin_phase': 0.0,
            'Ey_origin_phase': 0.0,
            'Ez_origin_phase': 0.0
        },
        'frame_rotation': {
            'theta_x': -33.5, # Angle de rotation X (degrés)
            'theta_y': 33.5, # Angle de rotation Y (degrés)
            'theta_z': 0  # Angle de rotation Z (degrés)
        }
    })
    
    # État des compensations (activation/désactivation)
    compensation_active: Dict[str, bool] = field(default_factory=lambda: {
        'offset_exc_off': True,
        'offset_exc_on': False,
        'user_offset': False,
        'phase': True,
        'frame_rotation': False
    })


class PostProcessingManager:

    # === INITIALISATION ===
    def __init__(self):
        """Initialise le manager avec configuration et buffer unique"""
        self.config = PostProcessingConfig()
        
        # Quaternion de rotation
        self._rotation_quaternion = None
        self._rotation_quaternion_inv = None
        self._update_rotation_quaternion()
        self.current_mode = 'exploration'
        # Initialiser le buffer
        self.processed_data_buffer = AdaptiveDataBuffer(max_size=100)
        
        # Configuration avec noms personnalisables
        self.config.compensation_storage = {
            'offset_exc_off': {
                'Ex_real': 0.0, 'Ex_imag': 0.0,
                'Ey_real': 0.0, 'Ey_imag': 0.0,
                'Ez_real': 0.0, 'Ez_imag': 0.0
            },
            'offset_exc_on': {
                'Ex_real': 0.0, 'Ex_imag': 0.0,
                'Ey_real': 0.0, 'Ey_imag': 0.0,
                'Ez_real': 0.0, 'Ez_imag': 0.0
            },
            'user_offset': {
                'Ex_real': 0.0, 'Ex_imag': 0.0,
                'Ey_real': 0.0, 'Ey_imag': 0.0,
                'Ez_real': 0.0, 'Ez_imag': 0.0
            },
            'phase_corrections': {'Ex_origin_phase': 0.0, 'Ey_origin_phase': 0.0, 'Ez_origin_phase': 0.0},
            'frame_rotation': {'theta_x': -33.5, 'theta_y': 33.5, 'theta_z': 0}
        }

        self.config.compensation_active = {
            'offset_exc_off': True,
            'offset_exc_on': True,
            'user_offset': False,
            'phase': True,
            'frame_rotation': False
        }


    # === METHODES POUR GERER LES BUFFERS DE DONNÉES ===
    
    def add_sample(self, sample: AcquisitionSample):
        """Ajoute un échantillon après traitement"""
        processed_sample = self._process_sample(sample)
        self.processed_data_buffer.append_sample(processed_sample)
        
        # Debug: vérifier l'état du buffer
        #buffer_info = self.processed_data_buffer.get_buffer_info()
        #print(f"[POST] Buffer: {buffer_info.get('current_size', 0)}/{buffer_info.get('max_size', 100)} échantillons")
        
        return processed_sample  # Retourner l'échantillon traité

    def get_latest_samples(self, n=1):
        """Récupère les derniers échantillons traités"""
        return self.processed_data_buffer.get_latest_samples(n)

    # === METHODES POUR CALCULER LES COMPENSATIONS ===
    def calibrate_phase(self, samples: List[AcquisitionSample]) -> Dict[str, float]:
        """
        Calcule et stocke les corrections de phase en minimisant la partie imaginaire.
        
        Args:
            samples: Liste d'échantillons acquis sans excitation (environnement de référence)
            
        Returns:
            Dict avec les angles de correction optimaux pour Ex, Ey, Ez (en radians)
        """
        if not samples:
            # Valeurs par défaut si pas d'échantillons
            default_corrections = {'Ex_origin_phase': 0.0, 'Ey_origin_phase': 0.0, 'Ez_origin_phase': 0.0}
            self.config.compensation_storage['phase_corrections'] = default_corrections
            return default_corrections
        
        # Extraction des données en arrays numpy pour efficacité
        ex_real = np.array([s.adc1_ch1 for s in samples])
        ex_imag = np.array([s.adc1_ch2 for s in samples])
        ey_real = np.array([s.adc1_ch3 for s in samples])
        ey_imag = np.array([s.adc1_ch4 for s in samples])
        ez_real = np.array([s.adc2_ch1 for s in samples])
        ez_imag = np.array([s.adc2_ch2 for s in samples])
        
        # Calcul des angles initiaux (estimation grossière)
        initial_phases = {
            'Ex': math.atan2(np.mean(ex_imag), np.mean(ex_real)),
            'Ey': math.atan2(np.mean(ey_imag), np.mean(ey_real)),
            'Ez': math.atan2(np.mean(ez_imag), np.mean(ez_real))
        }
        
        # Optimisation pour chaque axe
        def objective_mean_squared(phase, real_data, imag_data):
            """Minimise le carré de la moyenne de la partie imaginaire"""
            cos_phi = np.cos(phase)
            sin_phi = np.sin(phase)
            imag_rotated = -real_data * sin_phi + imag_data * cos_phi  # Cohérent avec apply_rotation (signe ajusté)
            mean_imag = np.mean(imag_rotated)
            return mean_imag ** 2
        
        optimized_phases = {}
        
        # Ex - Optimisation individuelle
        result_ex = minimize_scalar(
            lambda p: objective_mean_squared(p, ex_real, ex_imag),
            bounds=(initial_phases['Ex'] - np.pi, initial_phases['Ex'] + np.pi),
            method='bounded'
        )
        optimized_phases['Ex_origin_phase'] = result_ex.x
        
        # Ey - Optimisation individuelle
        result_ey = minimize_scalar(
            lambda p: objective_mean_squared(p, ey_real, ey_imag),
            bounds=(initial_phases['Ey'] - np.pi, initial_phases['Ey'] + np.pi),
            method='bounded'
        )
        optimized_phases['Ey_origin_phase'] = result_ey.x
        
        # Ez - Optimisation individuelle
        result_ez = minimize_scalar(
            lambda p: objective_mean_squared(p, ez_real, ez_imag),
            bounds=(initial_phases['Ez'] - np.pi, initial_phases['Ez'] + np.pi),
            method='bounded'
        )
        optimized_phases['Ez_origin_phase'] = result_ez.x
        
        # Debug : afficher l'amélioration
        print(f"[POST] Phase Ex: initial={math.degrees(initial_phases['Ex']):.1f}°, "
            f"optimisé={math.degrees(optimized_phases['Ex_origin_phase']):.1f}°")
        print(f"[POST] Phase Ey: initial={math.degrees(initial_phases['Ey']):.1f}°, "
            f"optimisé={math.degrees(optimized_phases['Ey_origin_phase']):.1f}°")
        print(f"[POST] Phase Ez: initial={math.degrees(initial_phases['Ez']):.1f}°, "
            f"optimisé={math.degrees(optimized_phases['Ez_origin_phase']):.1f}°")
        
        # Test : calcul de la partie imaginaire résiduelle moyenne
        for axis, (real, imag, phase_key) in [
            ('Ex', (ex_real, ex_imag, 'Ex_origin_phase')),
            ('Ey', (ey_real, ey_imag, 'Ey_origin_phase')),
            ('Ez', (ez_real, ez_imag, 'Ez_origin_phase'))
        ]:
            phase = optimized_phases[phase_key]
            
            # Calcul avant correction
            imag_before = np.mean(imag)
            
            # Calcul après correction (cohérent avec apply_rotation)
            imag_after = np.mean(-real * np.sin(phase) + imag * np.cos(phase))
            
            print(f"[POST] {axis} - Partie imaginaire moyenne:")
            print(f"  Avant correction: {imag_before:.4f}")
            print(f"  Après correction: {imag_after:.4f}")
            print(f"  Amélioration: {abs(imag_before) - abs(imag_after):.4f}")
        
        # Stockage dans la configuration
        self.config.compensation_storage['phase_corrections'] = optimized_phases
        
        return optimized_phases
    
    def calibrate_offset(self, samples: List[AcquisitionSample], offset_key: str) -> Dict[str, float]:
        """Calibration offset avec désactivation temporaire de la cible"""
        print(f"\n[CALIBRATION] Calibration {offset_key}")
        

        # Désactiver temporairement l'offset cible
        self.config.compensation_active[offset_key] = False
        
        

        # Calcul sur les valeurs finales (sans l'offset cible)
        offsets = {
            'Ex_real': np.mean([s.adc1_ch1 for s in samples]),
            'Ex_imag': np.mean([s.adc1_ch2 for s in samples]),
            'Ey_real': np.mean([s.adc1_ch3 for s in samples]),
            'Ey_imag': np.mean([s.adc1_ch4 for s in samples]),
            'Ez_real': np.mean([s.adc2_ch1 for s in samples]),
            'Ez_imag': np.mean([s.adc2_ch2 for s in samples])
        }
        
        # Stocker les valeurs calculées
        self.config.compensation_storage[offset_key] = offsets
        

        
        print(f"[CALIBRATION] {offset_key} calculé: {offsets}")
        return offsets
    
    def start_calibration_renewal(self, compensation_key: str):
        """Démarre une calibration avec désactivation et régénération du buffer"""
        print(f"[POST] Démarrage calibration: {compensation_key}")
        
        # Map keys if necessary
        if compensation_key == 'phase':
            compensation_key = 'phase_corrections'
        
        # Save current state
        self._calibration_state = {
            'key': compensation_key,
            'active': True,
            'original_active': self.config.compensation_active.get(compensation_key, False),
            'original_values': self.config.compensation_storage.get(compensation_key, {}).copy()
        }
        
        # Temporarily disable the compensation
        if compensation_key in self.config.compensation_active:
            self.config.compensation_active[compensation_key] = False
            print(f"[POST] Compensation {compensation_key} désactivée temporairement")
        
        # Clear buffer
        self.processed_data_buffer.clear_buffer()
        print(f"[POST] Buffer vidé, en attente de remplissage...")

    def is_calibration_complete(self) -> bool:
        """Vérifie si le buffer est suffisamment rempli pour la calibration"""
        if not hasattr(self, '_calibration_state') or not self._calibration_state['active']:
            return False
        
        info = self.processed_data_buffer.get_buffer_info()
        current_size = info.get('current_size', 0)
        max_size = info.get('max_size', 100)
        
        # Consider complete when buffer is 80% full
        is_complete = current_size >= (max_size*0.8)
        
        if is_complete:
            print(f"[POST] Buffer rempli à {current_size}/{max_size}")
        
        return is_complete

    def complete_calibration(self) -> dict:
        """Finalise la calibration et retourne les résultats"""
        if not hasattr(self, '_calibration_state') or not self._calibration_state['active']:
            return {}
        
        cal_key = self._calibration_state['key']
        print(f"[POST] Finalisation calibration: {cal_key}")
        
        # Get all samples from buffer
        samples = self.processed_data_buffer.get_all_samples()
        
        if not samples:
            print(f"[POST] Erreur: buffer vide pour calibration {cal_key}")
            # Restore original state
            self.config.compensation_active[cal_key] = self._calibration_state['original_active']
            del self._calibration_state
            return {}
        
        # Call internal methods for calculation
        result = {}
        
        if cal_key in ['offset_exc_off', 'offset_exc_on', 'user_offset']:
            # Use existing calibrate_offset
            result = self.calibrate_offset(samples, cal_key)
            
        elif cal_key == 'phase_corrections':
            # Use existing calibrate_phase
            result = self.calibrate_phase(samples)
        
        # Reactivate compensation
        self.config.compensation_active[cal_key] = True
        print(f"[POST] Calibration terminée: {cal_key} = {result}")
        
        # Clean up state
        del self._calibration_state
        
        return result
    
    
    # === METHODES DE TRAITEMENT ===
    def _process_sample(self, sample: AcquisitionSample) -> AcquisitionSample:
        """Traitement avec détection automatique des offsets - ORDRE CORRIGÉ"""
        processed_sample = sample
        

        # Offset sans excitation
        if self.is_compensation_active('offset_exc_off'):
            processed_sample = self._apply_offset_correction(processed_sample, 'offset_exc_off')
            #print("[DEBUG PROCESS] Offset sans excitation appliqué")

        if self.is_compensation_active('phase'):
            processed_sample = self._apply_phase_correction(processed_sample)

        
        # Offset avec excitation
        if self.is_compensation_active('offset_exc_on'):
            processed_sample = self._apply_offset_correction(processed_sample, 'offset_exc_on')
            #print("[DEBUG PROCESS] Offset avec excitation appliqué")

        if self.is_compensation_active('frame_rotation'):
            processed_sample = self._rotate_sample(processed_sample)
        
        
        return processed_sample

    def process_buffer(self, samples: List[AcquisitionSample], frequency: float = None) -> List[AcquisitionSample]:
        """
        Applique le post-processing complet sur un buffer d'échantillons.
        
        Args:
            samples: Liste d'échantillons bruts
            frequency: Fréquence actuelle pour la compensation parasites
            
        Returns:
            Liste d'échantillons traités
        """
        processed_samples = []
        for sample in samples:
            processed_samples.append(self._process_sample(sample))
        return processed_samples
    

    # === METHODES POUR GERER LA CONFIGURATION DU DATA PROCESSEUR ===

    def update_config(self, **kwargs):
        """Met à jour la configuration avec gestion du storage"""
        for key, value in kwargs.items():
            if key in ['theta_x', 'theta_y', 'theta_z']:
                self.config.compensation_storage['frame_rotation'][key] = value
            elif key in self.config.compensation_active:
                self.config.compensation_active[key] = value
            elif key in self.config.compensation_storage:
                self.config.compensation_storage[key] = value
        
        # Mise à jour du quaternion si angles modifiés
        if any(k in kwargs for k in ['theta_x', 'theta_y', 'theta_z']):
            self._update_rotation_quaternion()
    
    def get_compensation_state(self) -> dict:
        """Retourne l'état actuel des compensations"""
        return self.compensation_active.copy()
    
    def is_compensation_active(self, compensation_type: str) -> bool:
        """Vérifie si une compensation est active"""
        return self.config.compensation_active.get(compensation_type, False) 

    def get_processing_info(self) -> dict:
        """Retourne l'état avec détection automatique des offsets"""
        buffer_size = 0
        if hasattr(self, 'processed_data_buffer') and self.processed_data_buffer:
            buffer_info = self.config.compensation_storage.get('buffer_info', {})
            buffer_size = buffer_info.get('current_size', 0)
        
        info = {
            'phase': {
                'active': self.is_compensation_active('phase'),
                'values': self.config.compensation_storage['phase_corrections']
            },
            'frame_rotation': {
                'active': self.is_compensation_active('frame_rotation'),
                'values': self.config.compensation_storage['frame_rotation']
            },
            'buffer_size': buffer_size
        }
        
        # Ajouter tous les offsets dynamiquement
        for key in self.config.compensation_storage.keys():
            if key in self.config.compensation_active:
                info[key] = {
                    'active': self.is_compensation_active(key),
                    'values': self.config.compensation_storage[key]
                }
        
        return info

    def get_post_processing_info(self) -> dict:
        """Retourne l'état complet avec les nouveaux offsets"""
        buffer_size = 0
        if hasattr(self, 'processed_data_buffer') and self.processed_data_buffer:
            buffer_info = self.processed_data_buffer.get_buffer_info()
            buffer_size = buffer_info.get('current_size', 0)
        
        info = {
            'phase': {
                'active': self.is_compensation_active('phase'),
                'values': self.config.compensation_storage['phase_corrections']
            },
            'frame_rotation': {
                'active': self.is_compensation_active('frame_rotation'),
                'values': self.config.compensation_storage['frame_rotation']
            },
            'buffer_size': buffer_size
        }
        
        # Ajouter les offsets numérotés
        for i in range(1, 3):
            offset_key = f'offset_{i}'
            info[offset_key] = {
                'active': self.is_compensation_active(offset_key),
                'values': self.config.compensation_storage[offset_key]
            }
        
        return info

# Ajouter dans PostProcessingManager

    def toggle_compensation(self, compensation_type: str, enabled: bool):
        """Active/désactive une compensation spécifique"""
        if compensation_type in self.config.compensation_active:
            self.config.compensation_active[compensation_type] = enabled
            print(f"[POST] {compensation_type} {'activé' if enabled else 'désactivé'}")
    


    # ===============================================
    # METHODES INTERNES 
    # ===============================================

    def get_offset_keys(self) -> List[str]:
        """Retourne toutes les clés d'offsets disponibles"""
        return [key for key in self.config.compensation_storage.keys() 
                if key.endswith('_offset') or 'offset' in key.lower()]

    def _apply_offset_correction(self, sample: AcquisitionSample, offset_key: str) -> AcquisitionSample:
        """Application d'un offset par clé"""
        if not self.is_compensation_active(offset_key):
            return sample
        
        offsets = self.config.compensation_storage[offset_key]
        # print("[PostProcessing] offset_key", offset_key)
        # print("[PostProcessing] offsets", offsets)

        return AcquisitionSample(
            timestamp=sample.timestamp,
            adc1_ch1=int(sample.adc1_ch1 - offsets.get('Ex_real', 0.0)),
            adc1_ch2=int(sample.adc1_ch2 - offsets.get('Ex_imag', 0.0)),
            adc1_ch3=int(sample.adc1_ch3 - offsets.get('Ey_real', 0.0)),
            adc1_ch4=int(sample.adc1_ch4 - offsets.get('Ey_imag', 0.0)),
            adc2_ch1=int(sample.adc2_ch1 - offsets.get('Ez_real', 0.0)),
            adc2_ch2=int(sample.adc2_ch2 - offsets.get('Ez_imag', 0.0)),
            adc2_ch3=sample.adc2_ch3,
            adc2_ch4=sample.adc2_ch4
        )
    
    def _apply_phase_correction(self, sample: AcquisitionSample) -> AcquisitionSample:
        try:
            # print("[DEBUG PHASE] Active:", self.is_compensation_active('phase'))
            if not self.is_compensation_active('phase'):
                return sample
            
            ex_real = sample.adc1_ch1
            ex_imag = sample.adc1_ch2
            ey_real = sample.adc1_ch3
            ey_imag = sample.adc1_ch4
            ez_real = sample.adc2_ch1
            ez_imag = sample.adc2_ch2
            
            #print(f"[DEBUG PHASE] Initial: Ex({ex_real}+j{ex_imag}), Ey({ey_real}+j{ey_imag}), Ez({ez_real}+j{ez_imag})")
            
            corrections = self.config.compensation_storage.get('phase_corrections', {})
            #print(f"[DEBUG PHASE] Corrections rad: {corrections}, deg: { {k: math.degrees(v) for k,v in corrections.items()} }")
            
            def apply_rotation(real, imag, phi):
                if phi == 0:
                    return real, imag
                cos_phi = math.cos(phi)
                sin_phi = math.sin(phi)
                real_new = real * cos_phi - imag * sin_phi
                imag_new = -real * sin_phi + imag * cos_phi  # Cohérent avec calibration (signe ajusté)
                
                # Vérif annulation (tolérance pour bruit)
                #if abs(imag_new) > 1e-3 * abs(real_new):
                    #print("[WARNING PHASE] Imag non annulé (bruit élevé)")
                
                return real_new, imag_new
            
            ex_real, ex_imag = apply_rotation(ex_real, ex_imag, corrections.get('Ex_origin_phase', 0.0))
            ey_real, ey_imag = apply_rotation(ey_real, ey_imag, corrections.get('Ey_origin_phase', 0.0))
            ez_real, ez_imag = apply_rotation(ez_real, ez_imag, corrections.get('Ez_origin_phase', 0.0))
            
            #print(f"[DEBUG PHASE] Après: Ex({ex_real}+j{ex_imag}), Ey({ey_real}+j{ey_imag}), Ez({ez_real}+j{ez_imag})")
            
            # Vérif magnitude
            for axis, r_i, i_i, r_n, i_n in [('Ex', sample.adc1_ch1, sample.adc1_ch2, ex_real, ex_imag), 
                                              ('Ey', sample.adc1_ch3, sample.adc1_ch4, ey_real, ey_imag), 
                                              ('Ez', sample.adc2_ch1, sample.adc2_ch2, ez_real, ez_imag)]:
                mag_init = math.sqrt(r_i**2 + i_i**2)
                mag_new = math.sqrt(r_n**2 + i_n**2)
                #print(f"[DEBUG PHASE] Magnitude {axis}: init={mag_init:.2f}, new={mag_new:.2f}, diff={mag_new - mag_init:.2f}")
            
            return AcquisitionSample(
                timestamp=sample.timestamp,
                adc1_ch1=int(ex_real),
                adc1_ch2=int(ex_imag),
                adc1_ch3=int(ey_real),
                adc1_ch4=int(ey_imag),
                adc2_ch1=int(ez_real),
                adc2_ch2=int(ez_imag),
                adc2_ch3=sample.adc2_ch3,
                adc2_ch4=sample.adc2_ch4
            )
            
        except Exception as e:
            print(f"[ERROR] Correction phase : {e}")
            return sample

    # === METHODES DE ROTATION ===

    def _rotate_sample(self, sample: AcquisitionSample) -> AcquisitionSample:
        """Applique la rotation de référentiel au sample"""
        # Extraction des composantes Ex, Ey, Ez (parties réelles pour la rotation géométrique)
        ex_real = sample.adc1_ch1
        ey_real = sample.adc1_ch3  
        ez_real = sample.adc2_ch1
        
        # Rotation du vecteur E_real
        ex_rot, ey_rot, ez_rot = self._rotate_vector(ex_real, ey_real, ez_real, to_bench_frame=True)
        
        # Extraction des composantes imaginaires
        ex_imag = sample.adc1_ch2
        ey_imag = sample.adc1_ch4
        ez_imag = sample.adc2_ch2
        
        # Rotation du vecteur E_imag
        ex_imag_rot, ey_imag_rot, ez_imag_rot = self._rotate_vector(ex_imag, ey_imag, ez_imag, to_bench_frame=True)
        
        # Création du sample avec les valeurs tournées
        return AcquisitionSample(
            timestamp=sample.timestamp,
            adc1_ch1=int(ex_rot),
            adc1_ch2=int(ex_imag_rot),
            adc1_ch3=int(ey_rot),
            adc1_ch4=int(ey_imag_rot),
            adc2_ch1=int(ez_rot),
            adc2_ch2=int(ez_imag_rot),
            adc2_ch3=sample.adc2_ch3,  # Canaux auxiliaires non modifiés
            adc2_ch4=sample.adc2_ch4
        )
    
    def _update_rotation_quaternion(self):
        """Met à jour le quaternion avec les angles du storage"""
        rotation_angles = self.config.compensation_storage['frame_rotation']
        
        # Utiliser les angles du storage
        theta_x = rotation_angles.get('theta_x', -45.0)
        theta_y = rotation_angles.get('theta_y')
        if theta_y is None:
            theta_y = -math.degrees(math.atan(1/math.sqrt(2)))
        
        theta_z = rotation_angles.get('theta_z', 0.0)
        
        # Conversion et calcul des quaternions (logique existante)
        theta_x_rad = math.radians(theta_x)
        theta_y_rad = math.radians(theta_y)
        theta_z_rad = math.radians(theta_z)
        
        # Quaternions pour chaque rotation
        qx = np.array([math.cos(theta_x_rad/2), math.sin(theta_x_rad/2), 0, 0])
        qy = np.array([math.cos(theta_y_rad/2), 0, math.sin(theta_y_rad/2), 0])
        qz = np.array([math.cos(theta_z_rad/2), 0, 0, math.sin(theta_z_rad/2)])
        
        # Composition : q = qz * qy * qx
        q_temp = self._quaternion_multiply(qy, qx)
        self._rotation_quaternion = self._quaternion_multiply(qz, q_temp)
        
        # Quaternion inverse (conjugué pour rotation unitaire)
        self._rotation_quaternion_inv = np.array([
            self._rotation_quaternion[0],
            -self._rotation_quaternion[1],
            -self._rotation_quaternion[2],
            -self._rotation_quaternion[3]
        ])
    
    def _quaternion_multiply(self, q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
        """Multiplie deux quaternions"""
        w1, x1, y1, z1 = q1
        w2, x2, y2, z2 = q2
        
        return np.array([
            w1*w2 - x1*x2 - y1*y2 - z1*z2,
            w1*x2 + x1*w2 + y1*z2 - z1*y2,
            w1*y2 - x1*z2 + y1*w2 + z1*x2,
            w1*z2 + x1*y2 - y1*x2 + z1*w2
        ])
    
    def _quaternion_rotate(self, q: np.ndarray, v: np.ndarray) -> np.ndarray:
        """Applique une rotation quaternion à un vecteur"""
        # Conversion vecteur en quaternion pur
        v_quat = np.array([0, v[0], v[1], v[2]])
        
        # Rotation : v' = q * v * q^(-1)
        temp = self._quaternion_multiply(q, v_quat)
        rotated = self._quaternion_multiply(temp, self._rotation_quaternion_inv if np.array_equal(q, self._rotation_quaternion) else self._rotation_quaternion)
        
        # Extraction de la partie vectorielle
        return rotated[1:4]
    
    def _rotate_vector(self, x: float, y: float, z: float, to_bench_frame: bool = True) -> Tuple[float, float, float]:
        """Applique la rotation à un vecteur"""
        vector = np.array([x, y, z])
        
        if to_bench_frame:
            # Sensor → Bench
            rotated = self._quaternion_rotate(self._rotation_quaternion, vector)
        else:
            # Bench → Sensor
            rotated = self._quaternion_rotate(self._rotation_quaternion_inv, vector)
        
        return tuple(rotated)
