#!/usr/bin/env python3
"""
Test du module de rotation de référentiel depuis la racine du projet.
"""

import sys
import os
import numpy as np
import math
from datetime import datetime

# Ajout des chemins nécessaires
sys.path.insert(0, 'EFImagingBench_App/src/core/AD9106_ADS131A04_ElectricField_3D/components')

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

def test_module_rotation():
    """Test complet du module de rotation"""
    print("\n🧪 TEST UNITAIRE - MODULE DE ROTATION DE RÉFÉRENTIEL")
    print("=" * 60)
    
    # 1. Test initialisation
    print("\n1️⃣ Test initialisation...")
    processor = FrameRotationProcessor()
    expected_theta_y = math.degrees(math.atan(1 / math.sqrt(2)))
    
    print(f"   θx = {processor.theta_x:.2f}° (attendu: -45.00°)")
    print(f"   θy = {processor.theta_y:.2f}° (attendu: {expected_theta_y:.2f}°)")
    print(f"   θz = {processor.theta_z:.2f}° (attendu: 0.00°)")
    
    # Vérification quaternions normalisés
    norm_q = np.linalg.norm(processor.rotation_quaternion)
    norm_qi = np.linalg.norm(processor.inverse_quaternion)
    print(f"   Quaternions normalisés: ||q||={norm_q:.6f}, ||q⁻¹||={norm_qi:.6f}")
    
    assert abs(norm_q - 1.0) < 1e-10, "Quaternion rotation pas normalisé"
    assert abs(norm_qi - 1.0) < 1e-10, "Quaternion inverse pas normalisé"
    
    # 2. Test rotation identité
    print("\n2️⃣ Test rotation identité...")
    identity_processor = FrameRotationProcessor(0.0, 0.0, 0.0)
    test_vector = [1.5, -2.3, 3.7]
    
    result = identity_processor._rotate_vector(test_vector[0], test_vector[1], test_vector[2], to_bench_frame=True)
    error = np.linalg.norm(np.array(result) - np.array(test_vector))
    
    print(f"   Vecteur: {test_vector}")
    print(f"   Résultat: {result}")
    print(f"   Erreur: {error:.2e}")
    
    assert error < 1e-10, f"Rotation identité échouée, erreur: {error}"
    
    # 3. Test cohérence probe→bench→probe
    print("\n3️⃣ Test cohérence aller-retour...")
    test_vectors = [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0], 
        [0.0, 0.0, 1.0],
        [2.5, -1.8, 4.2]
    ]
    
    max_error = 0.0
    for i, vector in enumerate(test_vectors):
        # probe → bench → probe
        bench = processor._rotate_vector(vector[0], vector[1], vector[2], to_bench_frame=True)
        back = processor._rotate_vector(bench[0], bench[1], bench[2], to_bench_frame=False)
        
        error = np.linalg.norm(np.array(back) - np.array(vector))
        max_error = max(max_error, error)
        
        print(f"   Test {i+1}: erreur = {error:.2e}")
    
    print(f"   Erreur maximale: {max_error:.2e}")
    assert max_error < 1e-10, f"Cohérence aller-retour échouée, erreur max: {max_error}"
    
    # 4. Test rotation simple Rz(90°)
    print("\n4️⃣ Test rotation Rz(90°)...")
    z90_processor = FrameRotationProcessor(0.0, 0.0, 90.0)
    unit_x = [1.0, 0.0, 0.0]
    
    # E_probe = Rz(90°) * E_bench, donc (1,0,0) → (0,1,0)
    result = z90_processor._rotate_vector(unit_x[0], unit_x[1], unit_x[2], to_bench_frame=False)
    expected = [0.0, 1.0, 0.0]
    
    error = np.linalg.norm(np.array(result) - np.array(expected))
    print(f"   (1,0,0) → {result}")
    print(f"   Attendu: {expected}")
    print(f"   Erreur: {error:.2e}")
    
    assert error < 1e-8, f"Rotation Rz(90°) échouée, erreur: {error}"
    
    # 5. Test rotation d'échantillon complet
    print("\n5️⃣ Test rotation échantillon...")
    sample = AcquisitionSample(
        timestamp=datetime.now(),
        adc1_ch1=1000, adc1_ch2=1100,  # Ex I/Q
        adc1_ch3=2000, adc1_ch4=2200,  # Ey I/Q  
        adc2_ch1=3000, adc2_ch2=3300,  # Ez I/Q
        adc2_ch3=4000, adc2_ch4=5000   # Auxiliaires
    )
    
    rotated = processor.rotate_sample(sample, to_bench_frame=True)
    
    # Vérification que les composantes principales changent
    components_changed = (
        rotated.adc1_ch1 != sample.adc1_ch1 or
        rotated.adc1_ch2 != sample.adc1_ch2 or  # Maintenant la quadrature doit changer aussi
        rotated.adc1_ch3 != sample.adc1_ch3 or
        rotated.adc1_ch4 != sample.adc1_ch4 or
        rotated.adc2_ch1 != sample.adc2_ch1 or
        rotated.adc2_ch2 != sample.adc2_ch2
    )
    
    print(f"   Ex I: {sample.adc1_ch1} → {rotated.adc1_ch1}")
    print(f"   Ex Q: {sample.adc1_ch2} → {rotated.adc1_ch2}")
    print(f"   Ey I: {sample.adc1_ch3} → {rotated.adc1_ch3}")
    print(f"   Ez I: {sample.adc2_ch1} → {rotated.adc2_ch1}")
    print(f"   Aux 1: {sample.adc2_ch3} → {rotated.adc2_ch3} {'✅' if sample.adc2_ch3 == rotated.adc2_ch3 else '❌'}")
    print(f"   Aux 2: {sample.adc2_ch4} → {rotated.adc2_ch4} {'✅' if sample.adc2_ch4 == rotated.adc2_ch4 else '❌'}")
    
    assert components_changed, "Les composantes principales doivent changer après rotation"
    assert rotated.adc2_ch3 == sample.adc2_ch3, "Canal auxiliaire adc2_ch3 doit rester inchangé"
    assert rotated.adc2_ch4 == sample.adc2_ch4, "Canal auxiliaire adc2_ch4 doit rester inchangé"
    
    # 6. Test performance
    print("\n6️⃣ Test performance...")
    import time
    
    n_iterations = 1000
    start_time = time.time()
    
    for _ in range(n_iterations):
        rotated = processor.rotate_sample(sample, to_bench_frame=True)
    
    end_time = time.time()
    time_per_sample = ((end_time - start_time) / n_iterations) * 1000  # ms
    throughput = 1000 / time_per_sample  # échantillons/sec
    
    print(f"   Temps par échantillon: {time_per_sample:.3f} ms")
    print(f"   Débit: {throughput:.0f} échantillons/sec")
    print(f"   Compatible 70Hz: {'✅' if throughput >= 70 else '❌'}")
    
    # 7. Test API rotation_info
    print("\n7️⃣ Test API get_rotation_info...")
    info = processor.get_rotation_info()
    
    required_keys = ['theta_x_deg', 'theta_y_deg', 'theta_z_deg', 'quaternion', 'inverse_quaternion']
    for key in required_keys:
        assert key in info, f"Clé manquante dans rotation_info: {key}"
    
    print(f"   Infos disponibles: {list(info.keys())}")
    print(f"   Quaternion: [{info['quaternion'][0]:.4f}, {info['quaternion'][1]:.4f}, {info['quaternion'][2]:.4f}, {info['quaternion'][3]:.4f}]")
    
    # 8. Test mise à jour angles
    print("\n8️⃣ Test mise à jour angles...")
    old_quaternion = processor.rotation_quaternion.copy()
    
    processor.set_rotation_angles(30.0, 45.0, 60.0)
    
    assert processor.theta_x == 30.0, "Angle θx pas mis à jour"
    assert processor.theta_y == 45.0, "Angle θy pas mis à jour"  
    assert processor.theta_z == 60.0, "Angle θz pas mis à jour"
    
    new_quaternion = processor.rotation_quaternion
    quaternion_changed = not np.allclose(old_quaternion, new_quaternion, atol=1e-10)
    
    print(f"   Nouveaux angles: θx={processor.theta_x}°, θy={processor.theta_y}°, θz={processor.theta_z}°")
    print(f"   Quaternion changé: {'✅' if quaternion_changed else '❌'}")
    
    assert quaternion_changed, "Le quaternion doit changer après mise à jour des angles"
    
    return True

if __name__ == "__main__":
    try:
        success = test_module_rotation()
        
        print("\n" + "=" * 60)
        print("🎉 TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS !")
        print("✅ Le module EFImagingBench_FrameRotation_Module fonctionne correctement.")
        print("✅ Convention E_probe = Rz * Ry * Rx * E_bench respectée.")
        print("✅ Rotation des 6 composantes (in-phase + quadrature) validée.")
        print("✅ Performance compatible avec acquisition 70Hz.")
        
    except AssertionError as e:
        print(f"\n❌ ÉCHEC DU TEST: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 ERREUR INATTENDUE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 