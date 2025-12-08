#!/usr/bin/env python3
"""
Test unitaire complet pour le module EFImagingBench_FrameRotation_Module.

Tests de validation exhaustifs :
1. Rotations élémentaires autour de chaque axe (90°, 180°, 270°) 
2. Inversions des vecteurs de base de R³
3. Compositions de rotations élémentaires
4. Validation mathématique du groupe SO(3)
5. Tests de performance et robustesse
6. Tests métier (échantillons ADC complets)
7. Tests avec angles théoriques du projet

Auteur: Luis Saluden
Date: 2025-01-27
"""

import sys
import os
import numpy as np
import math
import time
from datetime import datetime

# Ajout du chemin pour les imports
current_dir = os.path.dirname(os.path.abspath(__file__))
components_path = os.path.join(current_dir, '..', '..', 'src', 'core', 'AD9106_ADS131A04_ElectricField_3D', 'components')
sys.path.insert(0, components_path)

# Test d'import
try:
    from EFImagingBench_FrameRotation_Module import FrameRotationProcessor
    from AD9106_ADS131A04_DataBuffer_Module import AcquisitionSample
    print("✅ Imports réussis")
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

class TestElementaryRotations:
    """Classe de test pour les rotations élémentaires"""
    
    def __init__(self):
        self.tolerance = 1e-12  # Tolérance pour les comparaisons
        self.base_vectors = {
            'x': np.array([1.0, 0.0, 0.0]),
            'y': np.array([0.0, 1.0, 0.0]),
            'z': np.array([0.0, 0.0, 1.0])
        }
        
    def rotate_vector(self, processor, vector, to_bench=False):
        """Helper pour appliquer une rotation à un vecteur"""
        result = processor._rotate_vector(vector[0], vector[1], vector[2], to_bench_frame=to_bench)
        return np.array(result)
    
    def assert_vectors_equal(self, result, expected, test_name):
        """Vérification avec tolérance et message d'erreur détaillé"""
        error = np.linalg.norm(result - expected)
        if error > self.tolerance:
            print(f"❌ {test_name}: ÉCHEC")
            print(f"   Résultat: [{result[0]:.6f}, {result[1]:.6f}, {result[2]:.6f}]")
            print(f"   Attendu:  [{expected[0]:.6f}, {expected[1]:.6f}, {expected[2]:.6f}]")
            print(f"   Erreur: {error:.2e}")
            return False
        else:
            print(f"✅ {test_name}: OK (erreur: {error:.2e})")
            return True

def test_rotations_x_axis():
    """Test des rotations élémentaires autour de l'axe X"""
    print("\n🔄 TEST ROTATIONS AUTOUR DE L'AXE X")
    print("=" * 50)
    
    tester = TestElementaryRotations()
    success_count = 0
    total_tests = 0
    
    # Test des rotations de 90°, 180°, 270° autour de X
    angles_tests = [
        (90.0, "Rx(90°)"),
        (180.0, "Rx(180°)"),
        (270.0, "Rx(270°)"),
        (-90.0, "Rx(-90°)")
    ]
    
    for angle, test_name in angles_tests:
        print(f"\n📐 {test_name}")
        processor = FrameRotationProcessor(angle, 0.0, 0.0)
        
        # Test vecteur X (doit rester inchangé)
        result_x = tester.rotate_vector(processor, tester.base_vectors['x'], to_bench=False)
        expected_x = tester.base_vectors['x']
        total_tests += 1
        if tester.assert_vectors_equal(result_x, expected_x, f"{test_name} - vecteur X"):
            success_count += 1
        
        # Test vecteur Y selon l'angle
        result_y = tester.rotate_vector(processor, tester.base_vectors['y'], to_bench=False)
        if angle == 90.0:
            expected_y = np.array([0.0, 0.0, 1.0])  # Y → Z
        elif angle == 180.0:
            expected_y = np.array([0.0, -1.0, 0.0])  # Y → -Y
        elif angle == 270.0 or angle == -90.0:
            expected_y = np.array([0.0, 0.0, -1.0])  # Y → -Z
        
        total_tests += 1
        if tester.assert_vectors_equal(result_y, expected_y, f"{test_name} - vecteur Y"):
            success_count += 1
        
        # Test vecteur Z selon l'angle
        result_z = tester.rotate_vector(processor, tester.base_vectors['z'], to_bench=False)
        if angle == 90.0:
            expected_z = np.array([0.0, -1.0, 0.0])  # Z → -Y
        elif angle == 180.0:
            expected_z = np.array([0.0, 0.0, -1.0])  # Z → -Z
        elif angle == 270.0 or angle == -90.0:
            expected_z = np.array([0.0, 1.0, 0.0])  # Z → Y
        
        total_tests += 1
        if tester.assert_vectors_equal(result_z, expected_z, f"{test_name} - vecteur Z"):
            success_count += 1
    
    print(f"\n📊 Bilan rotations X: {success_count}/{total_tests} tests réussis")
    return success_count == total_tests

def test_rotations_y_axis():
    """Test des rotations élémentaires autour de l'axe Y"""
    print("\n🔄 TEST ROTATIONS AUTOUR DE L'AXE Y")
    print("=" * 50)
    
    tester = TestElementaryRotations()
    success_count = 0
    total_tests = 0
    
    angles_tests = [
        (90.0, "Ry(90°)"),
        (180.0, "Ry(180°)"),
        (270.0, "Ry(270°)"),
        (-90.0, "Ry(-90°)")
    ]
    
    for angle, test_name in angles_tests:
        print(f"\n📐 {test_name}")
        processor = FrameRotationProcessor(0.0, angle, 0.0)
        
        # Test vecteur Y (doit rester inchangé)
        result_y = tester.rotate_vector(processor, tester.base_vectors['y'], to_bench=False)
        expected_y = tester.base_vectors['y']
        total_tests += 1
        if tester.assert_vectors_equal(result_y, expected_y, f"{test_name} - vecteur Y"):
            success_count += 1
        
        # Test vecteur X selon l'angle
        result_x = tester.rotate_vector(processor, tester.base_vectors['x'], to_bench=False)
        if angle == 90.0:
            expected_x = np.array([0.0, 0.0, -1.0])  # X → -Z
        elif angle == 180.0:
            expected_x = np.array([-1.0, 0.0, 0.0])  # X → -X
        elif angle == 270.0 or angle == -90.0:
            expected_x = np.array([0.0, 0.0, 1.0])  # X → Z
        
        total_tests += 1
        if tester.assert_vectors_equal(result_x, expected_x, f"{test_name} - vecteur X"):
            success_count += 1
        
        # Test vecteur Z selon l'angle
        result_z = tester.rotate_vector(processor, tester.base_vectors['z'], to_bench=False)
        if angle == 90.0:
            expected_z = np.array([1.0, 0.0, 0.0])  # Z → X
        elif angle == 180.0:
            expected_z = np.array([0.0, 0.0, -1.0])  # Z → -Z
        elif angle == 270.0 or angle == -90.0:
            expected_z = np.array([-1.0, 0.0, 0.0])  # Z → -X
        
        total_tests += 1
        if tester.assert_vectors_equal(result_z, expected_z, f"{test_name} - vecteur Z"):
            success_count += 1
    
    print(f"\n📊 Bilan rotations Y: {success_count}/{total_tests} tests réussis")
    return success_count == total_tests

def test_rotations_z_axis():
    """Test des rotations élémentaires autour de l'axe Z"""
    print("\n🔄 TEST ROTATIONS AUTOUR DE L'AXE Z")
    print("=" * 50)
    
    tester = TestElementaryRotations()
    success_count = 0
    total_tests = 0
    
    angles_tests = [
        (90.0, "Rz(90°)"),
        (180.0, "Rz(180°)"),
        (270.0, "Rz(270°)"),
        (-90.0, "Rz(-90°)")
    ]
    
    for angle, test_name in angles_tests:
        print(f"\n📐 {test_name}")
        processor = FrameRotationProcessor(0.0, 0.0, angle)
        
        # Test vecteur Z (doit rester inchangé)
        result_z = tester.rotate_vector(processor, tester.base_vectors['z'], to_bench=False)
        expected_z = tester.base_vectors['z']
        total_tests += 1
        if tester.assert_vectors_equal(result_z, expected_z, f"{test_name} - vecteur Z"):
            success_count += 1
        
        # Test vecteur X selon l'angle
        result_x = tester.rotate_vector(processor, tester.base_vectors['x'], to_bench=False)
        if angle == 90.0:
            expected_x = np.array([0.0, 1.0, 0.0])  # X → Y
        elif angle == 180.0:
            expected_x = np.array([-1.0, 0.0, 0.0])  # X → -X
        elif angle == 270.0 or angle == -90.0:
            expected_x = np.array([0.0, -1.0, 0.0])  # X → -Y
        
        total_tests += 1
        if tester.assert_vectors_equal(result_x, expected_x, f"{test_name} - vecteur X"):
            success_count += 1
        
        # Test vecteur Y selon l'angle
        result_y = tester.rotate_vector(processor, tester.base_vectors['y'], to_bench=False)
        if angle == 90.0:
            expected_y = np.array([-1.0, 0.0, 0.0])  # Y → -X
        elif angle == 180.0:
            expected_y = np.array([0.0, -1.0, 0.0])  # Y → -Y
        elif angle == 270.0 or angle == -90.0:
            expected_y = np.array([1.0, 0.0, 0.0])  # Y → X
        
        total_tests += 1
        if tester.assert_vectors_equal(result_y, expected_y, f"{test_name} - vecteur Y"):
            success_count += 1
    
    print(f"\n📊 Bilan rotations Z: {success_count}/{total_tests} tests réussis")
    return success_count == total_tests

def test_inversions_vectors():
    """Test des inversions complètes des vecteurs de base"""
    print("\n🔄 TEST INVERSIONS DES VECTEURS DE BASE")
    print("=" * 50)
    
    tester = TestElementaryRotations()
    success_count = 0
    total_tests = 0
    
    # Test inversion par rotation 180° autour de chaque axe
    inversions_tests = [
        # Inversion de X par rotation 180° autour Y ou Z
        ((0.0, 180.0, 0.0), "x", np.array([-1.0, 0.0, 0.0]), "Inversion X par Ry(180°)"),
        ((0.0, 0.0, 180.0), "x", np.array([-1.0, 0.0, 0.0]), "Inversion X par Rz(180°)"),
        
        # Inversion de Y par rotation 180° autour X ou Z
        ((180.0, 0.0, 0.0), "y", np.array([0.0, -1.0, 0.0]), "Inversion Y par Rx(180°)"),
        ((0.0, 0.0, 180.0), "y", np.array([0.0, -1.0, 0.0]), "Inversion Y par Rz(180°)"),
        
        # Inversion de Z par rotation 180° autour X ou Y
        ((180.0, 0.0, 0.0), "z", np.array([0.0, 0.0, -1.0]), "Inversion Z par Rx(180°)"),
        ((0.0, 180.0, 0.0), "z", np.array([0.0, 0.0, -1.0]), "Inversion Z par Ry(180°)"),
    ]
    
    for (theta_x, theta_y, theta_z), vector_name, expected, test_name in inversions_tests:
        processor = FrameRotationProcessor(theta_x, theta_y, theta_z)
        result = tester.rotate_vector(processor, tester.base_vectors[vector_name], to_bench=False)
        
        total_tests += 1
        if tester.assert_vectors_equal(result, expected, test_name):
            success_count += 1
    
    print(f"\n📊 Bilan inversions: {success_count}/{total_tests} tests réussis")
    return success_count == total_tests

def test_composition_rotations():
    """Test des compositions de rotations élémentaires"""
    print("\n🔄 TEST COMPOSITIONS DE ROTATIONS")
    print("=" * 50)
    
    tester = TestElementaryRotations()
    success_count = 0
    total_tests = 0
    
    # Test compositions non-triviales uniquement
    compositions_tests = [
        # Rx(90°) puis Rz(90°) : Z → (-Y) → X
        ((90.0, 0.0, 90.0), "z", np.array([1.0, 0.0, 0.0]), "Rz(90°)*Rx(90°) sur Z"),
        
        # Rx(90°) puis Ry(90°) : Y → Z → X  
        ((90.0, 90.0, 0.0), "y", np.array([1.0, 0.0, 0.0]), "Rx→Ry sur Y"),
        
        # Ry(90°) puis Rz(90°) : X → (-Z) → (-Z)
        ((0.0, 90.0, 90.0), "x", np.array([0.0, 0.0, -1.0]), "Ry→Rz sur X"),
        
        # Triple rotation séquentielle : X → X → (-Z) → (-Z)
        ((90.0, 90.0, 90.0), "x", np.array([0.0, 0.0, -1.0]), "Rx→Ry→Rz sur X"),
    ]
    
    for (theta_x, theta_y, theta_z), vector_name, expected, test_name in compositions_tests:
        processor = FrameRotationProcessor(theta_x, theta_y, theta_z)
        result = tester.rotate_vector(processor, tester.base_vectors[vector_name], to_bench=False)
        
        total_tests += 1
        if tester.assert_vectors_equal(result, expected, test_name):
            success_count += 1
    
    print(f"\n📊 Bilan compositions: {success_count}/{total_tests} tests réussis")
    return success_count == total_tests

def test_angle_equivalences():
    """Test des équivalences d'angles (360°, angles négatifs)"""
    print("\n🔄 TEST ÉQUIVALENCES D'ANGLES")
    print("=" * 50)
    
    tester = TestElementaryRotations()
    success_count = 0
    total_tests = 0
    
    # Test équivalences 360° = 0°
    processor_0 = FrameRotationProcessor(0.0, 0.0, 0.0)
    processor_360 = FrameRotationProcessor(360.0, 360.0, 360.0)
    
    for vector_name, vector in tester.base_vectors.items():
        result_0 = tester.rotate_vector(processor_0, vector, to_bench=False)
        result_360 = tester.rotate_vector(processor_360, vector, to_bench=False)
        
        total_tests += 1
        if tester.assert_vectors_equal(result_360, result_0, f"360° = 0° sur {vector_name}"):
            success_count += 1
    
    # Test équivalences angles négatifs
    equivalences = [
        ((-90.0, 0.0, 0.0), (270.0, 0.0, 0.0), "Rx(-90°) = Rx(270°)"),
        ((0.0, -90.0, 0.0), (0.0, 270.0, 0.0), "Ry(-90°) = Ry(270°)"),
        ((0.0, 0.0, -90.0), (0.0, 0.0, 270.0), "Rz(-90°) = Rz(270°)"),
    ]
    
    for (angles1, angles2, test_name) in equivalences:
        processor1 = FrameRotationProcessor(*angles1)
        processor2 = FrameRotationProcessor(*angles2)
        
        for vector_name, vector in tester.base_vectors.items():
            result1 = tester.rotate_vector(processor1, vector, to_bench=False)
            result2 = tester.rotate_vector(processor2, vector, to_bench=False)
            
            total_tests += 1
            if tester.assert_vectors_equal(result1, result2, f"{test_name} sur {vector_name}"):
                success_count += 1
    
    print(f"\n📊 Bilan équivalences: {success_count}/{total_tests} tests réussis")
    return success_count == total_tests

def test_orthogonality_preservation():
    """Test de la préservation de l'orthogonalité"""
    print("\n🔄 TEST PRÉSERVATION ORTHOGONALITÉ")
    print("=" * 50)
    
    tester = TestElementaryRotations()
    success_count = 0
    total_tests = 0
    
    # Test avec plusieurs rotations
    test_rotations = [
        (45.0, 0.0, 0.0),
        (0.0, 30.0, 0.0),
        (0.0, 0.0, 60.0),
        (-45.0, 35.26, 0.0),  # Angles théoriques du projet
        (90.0, 90.0, 90.0)
    ]
    
    for theta_x, theta_y, theta_z in test_rotations:
        processor = FrameRotationProcessor(theta_x, theta_y, theta_z)
        
        # Rotation des vecteurs de base
        x_rot = tester.rotate_vector(processor, tester.base_vectors['x'], to_bench=False)
        y_rot = tester.rotate_vector(processor, tester.base_vectors['y'], to_bench=False)
        z_rot = tester.rotate_vector(processor, tester.base_vectors['z'], to_bench=False)
        
        # Test orthogonalité (produit scalaire = 0)
        dot_xy = np.dot(x_rot, y_rot)
        dot_xz = np.dot(x_rot, z_rot)
        dot_yz = np.dot(y_rot, z_rot)
        
        total_tests += 3
        test_name_base = f"Orthogonalité θx={theta_x}°, θy={theta_y}°, θz={theta_z}°"
        
        if abs(dot_xy) < tester.tolerance:
            print(f"✅ {test_name_base} - X⊥Y: {dot_xy:.2e}")
            success_count += 1
        else:
            print(f"❌ {test_name_base} - X⊥Y: {dot_xy:.2e}")
            
        if abs(dot_xz) < tester.tolerance:
            print(f"✅ {test_name_base} - X⊥Z: {dot_xz:.2e}")
            success_count += 1
        else:
            print(f"❌ {test_name_base} - X⊥Z: {dot_xz:.2e}")
            
        if abs(dot_yz) < tester.tolerance:
            print(f"✅ {test_name_base} - Y⊥Z: {dot_yz:.2e}")
            success_count += 1
        else:
            print(f"❌ {test_name_base} - Y⊥Z: {dot_yz:.2e}")
        
        # Test conservation de la norme (vecteurs unitaires)
        norm_x = np.linalg.norm(x_rot)
        norm_y = np.linalg.norm(y_rot)
        norm_z = np.linalg.norm(z_rot)
        
        total_tests += 3
        for norm, name in [(norm_x, 'X'), (norm_y, 'Y'), (norm_z, 'Z')]:
            if abs(norm - 1.0) < tester.tolerance:
                print(f"✅ {test_name_base} - ||{name}|| = {norm:.6f}")
                success_count += 1
            else:
                print(f"❌ {test_name_base} - ||{name}|| = {norm:.6f}")
    
    print(f"\n📊 Bilan orthogonalité: {success_count}/{total_tests} tests réussis")
    return success_count == total_tests

def test_sample_rotation():
    """Test de rotation complète d'échantillons ADC"""
    print("\n🔄 TEST ROTATION ÉCHANTILLONS ADC")
    print("=" * 50)
    
    tester = TestElementaryRotations()
    success_count = 0
    total_tests = 0
    
    processor = FrameRotationProcessor()  # Angles théoriques
    
    # Test échantillon complet
    sample = AcquisitionSample(
        timestamp=datetime.now(),
        adc1_ch1=1000, adc1_ch2=1100,  # Ex I/Q
        adc1_ch3=2000, adc1_ch4=2200,  # Ey I/Q  
        adc2_ch1=3000, adc2_ch2=3300,  # Ez I/Q
        adc2_ch3=4000, adc2_ch4=5000   # Auxiliaires
    )
    
    # Rotation probe → bench
    rotated = processor.rotate_sample(sample, to_bench_frame=True)
    
    # Vérification que les composantes principales changent
    components_changed = (
        rotated.adc1_ch1 != sample.adc1_ch1 or
        rotated.adc1_ch2 != sample.adc1_ch2 or
        rotated.adc1_ch3 != sample.adc1_ch3 or
        rotated.adc1_ch4 != sample.adc1_ch4 or
        rotated.adc2_ch1 != sample.adc2_ch1 or
        rotated.adc2_ch2 != sample.adc2_ch2
    )
    
    total_tests += 1
    if components_changed:
        print("✅ Composantes principales modifiées après rotation")
        success_count += 1
    else:
        print("❌ Aucune composante principale modifiée")
    
    # Vérification préservation auxiliaires
    total_tests += 2
    if rotated.adc2_ch3 == sample.adc2_ch3:
        print("✅ Canal auxiliaire adc2_ch3 préservé")
        success_count += 1
    else:
        print("❌ Canal auxiliaire adc2_ch3 modifié")
        
    if rotated.adc2_ch4 == sample.adc2_ch4:
        print("✅ Canal auxiliaire adc2_ch4 préservé")
        success_count += 1
    else:
        print("❌ Canal auxiliaire adc2_ch4 modifié")
    
    # Test aller-retour
    back_to_probe = processor.rotate_sample(rotated, to_bench_frame=False)
    tolerance = 1  # 1 code ADC tolérance
    
    total_tests += 6
    for attr in ['adc1_ch1', 'adc1_ch2', 'adc1_ch3', 'adc1_ch4', 'adc2_ch1', 'adc2_ch2']:
        original_val = getattr(sample, attr)
        back_val = getattr(back_to_probe, attr)
        error = abs(back_val - original_val)
        
        if error <= tolerance:
            print(f"✅ Aller-retour {attr}: {original_val} → {back_val} (erreur: {error})")
            success_count += 1
        else:
            print(f"❌ Aller-retour {attr}: {original_val} → {back_val} (erreur: {error})")
    
    print(f"\n📊 Bilan échantillons: {success_count}/{total_tests} tests réussis")
    return success_count == total_tests

def test_performance():
    """Test de performance de rotation"""
    print("\n🔄 TEST PERFORMANCE")
    print("=" * 50)
    
    processor = FrameRotationProcessor()
    sample = AcquisitionSample(
        timestamp=datetime.now(),
        adc1_ch1=1000, adc1_ch2=2000, adc1_ch3=3000, adc1_ch4=4000,
        adc2_ch1=5000, adc2_ch2=6000, adc2_ch3=7000, adc2_ch4=8000
    )
    
    # Test performance
    n_iterations = 1000
    start_time = time.time()
    
    for _ in range(n_iterations):
        rotated = processor.rotate_sample(sample, to_bench_frame=True)
    
    end_time = time.time()
    time_per_sample = ((end_time - start_time) / n_iterations) * 1000  # ms
    throughput = 1000 / time_per_sample  # échantillons/sec
    
    print(f"   Temps par échantillon: {time_per_sample:.3f} ms")
    print(f"   Débit: {throughput:.0f} échantillons/sec")
    
    # Critères de performance
    compatible_70hz = throughput >= 70
    acceptable_latency = time_per_sample < 1.0
    
    print(f"   Compatible 70Hz: {'✅' if compatible_70hz else '❌'}")
    print(f"   Latence acceptable (<1ms): {'✅' if acceptable_latency else '❌'}")
    
    return compatible_70hz and acceptable_latency

def test_theoretical_angles():
    """Test avec les angles théoriques du projet"""
    print("\n🔄 TEST ANGLES THÉORIQUES PROJET")
    print("=" * 50)
    
    processor = FrameRotationProcessor()  # Angles par défaut
    
    # Vérification angles attendus
    expected_theta_y = math.degrees(math.atan(1 / math.sqrt(2)))
    
    angles_correct = (
        abs(processor.theta_x - (-45.0)) < 1e-6 and
        abs(processor.theta_y - expected_theta_y) < 1e-6 and
        abs(processor.theta_z - 0.0) < 1e-6
    )
    
    print(f"   θx = {processor.theta_x:.2f}° (attendu: -45.00°)")
    print(f"   θy = {processor.theta_y:.2f}° (attendu: {expected_theta_y:.2f}°)")
    print(f"   θz = {processor.theta_z:.2f}° (attendu: 0.00°)")
    print(f"   Angles théoriques: {'✅' if angles_correct else '❌'}")
    
    # Test transformations des axes
    axes = {'X': [1,0,0], 'Y': [0,1,0], 'Z': [0,0,1]}
    
    print("\n   Transformations sensor → bench:")
    for name, vector in axes.items():
        rotated = processor._rotate_vector(vector[0], vector[1], vector[2], to_bench_frame=True)
        print(f"   {name}: {vector} → [{rotated[0]:.3f}, {rotated[1]:.3f}, {rotated[2]:.3f}]")
    
    return angles_correct

def run_all_elementary_tests():
    """Lance tous les tests complets du module de rotation"""
    print("🧪 TESTS UNITAIRES COMPLETS - MODULE DE ROTATION DE RÉFÉRENTIEL")
    print("=" * 70)
    
    all_tests = [
        ("Rotations autour X", test_rotations_x_axis),
        ("Rotations autour Y", test_rotations_y_axis),
        ("Rotations autour Z", test_rotations_z_axis),
        ("Inversions vecteurs", test_inversions_vectors),
        ("Compositions", test_composition_rotations),
        ("Équivalences angles", test_angle_equivalences),
        ("Préservation orthogonalité", test_orthogonality_preservation),
        ("Rotation échantillons", test_sample_rotation),
        ("Performance", test_performance),
        ("Angles théoriques", test_theoretical_angles)
    ]
    
    results = []
    for test_name, test_func in all_tests:
        print(f"\n🎯 LANCEMENT: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
            status = "✅ RÉUSSI" if success else "❌ ÉCHEC"
            print(f"📋 {test_name}: {status}")
        except Exception as e:
            results.append((test_name, False))
            print(f"💥 {test_name}: ERREUR - {e}")
    
    # Bilan final
    print("\n" + "=" * 70)
    print("📊 BILAN FINAL DES TESTS ÉLÉMENTAIRES")
    print("=" * 70)
    
    successful_tests = sum(1 for _, success in results if success)
    total_tests = len(results)
    
    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 RÉSULTAT GLOBAL: {successful_tests}/{total_tests} groupes de tests réussis")
    
    if successful_tests == total_tests:
        print("🎉 TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS !")
        print("✅ Le module EFImagingBench_FrameRotation_Module est opérationnel.")
        print("✅ Propriétés mathématiques SO(3) validées.")
        print("✅ Performance compatible acquisition 70Hz.")
        print("✅ Rotation complète des échantillons ADC (in-phase + quadrature).")
        print("✅ Convention E_probe = Rz × Ry × Rx × E_bench respectée.")
        return True
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("⚠️  Le module nécessite des corrections avant utilisation.")
        return False

if __name__ == "__main__":
    try:
        success = run_all_elementary_tests()
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"\n💥 ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 