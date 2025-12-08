#!/usr/bin/env python3
"""
Test du système de segments pour le scan 2D
Vérifie la génération de trajectoire segmentée et le marquage des données
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from core.ArcusPerfomax4EXStage.components.EFImagingBench_Scan2D_Module import Scan2DConfigurator


def test_scan_segments():
    """Test la génération de segments pour un scan 2D"""
    print("=== Test génération de segments scan 2D ===")
    
    # Configuration d'un scan simple
    x_min, x_max = 0, 100
    y_min, y_max = 0, 50
    N = 3  # 3 lignes
    
    # Test mode E (unidirectionnel)
    print("\n--- Mode E (unidirectionnel) ---")
    scan_e = Scan2DConfigurator(x_min, x_max, y_min, y_max, N, mode='E')
    segments_e = scan_e.get_segmented_trajectory()
    
    print(f"Nombre de segments: {len(segments_e)}")
    for seg in segments_e:
        print(f"  {seg['id']}: {seg['type']} de {seg['start']} à {seg['end']}")
    
    # Vérifications
    scan_lines_e = [s for s in segments_e if s['type'] == 'scan_line']
    transitions_e = [s for s in segments_e if s['type'] == 'transition']
    assert len(scan_lines_e) == N, f"Attendu {N} lignes de scan, trouvé {len(scan_lines_e)}"
    print(f"✅ {len(scan_lines_e)} lignes de scan, {len(transitions_e)} transitions")
    
    # Test mode S (serpent)
    print("\n--- Mode S (serpent) ---")
    scan_s = Scan2DConfigurator(x_min, x_max, y_min, y_max, N, mode='S')
    segments_s = scan_s.get_segmented_trajectory()
    
    print(f"Nombre de segments: {len(segments_s)}")
    for seg in segments_s:
        print(f"  {seg['id']}: {seg['type']} de {seg['start']} à {seg['end']}")
    
    # Vérifications
    scan_lines_s = [s for s in segments_s if s['type'] == 'scan_line']
    transitions_s = [s for s in segments_s if s['type'] == 'transition']
    assert len(scan_lines_s) == N, f"Attendu {N} lignes de scan, trouvé {len(scan_lines_s)}"
    print(f"✅ {len(scan_lines_s)} lignes de scan, {len(transitions_s)} transitions")
    
    # Test conversion en points
    print("\n--- Conversion en points avec métadonnées ---")
    points = scan_e.get_points_from_segments(segments_e[:3])  # Premiers segments
    print(f"Nombre de points: {len(points)}")
    for i, (x, y, seg_info) in enumerate(points[:6]):  # Premiers points
        print(f"  Point {i}: ({x}, {y}) - segment {seg_info['id']} ({seg_info['type']})")


def test_segment_identification():
    """Test l'identification correcte des segments actifs vs transitions"""
    print("\n=== Test identification segments actifs ===")
    
    scan = Scan2DConfigurator(0, 100, 0, 50, 4, mode='S')
    segments = scan.get_segmented_trajectory()
    
    # Statistiques
    total_segments = len(segments)
    active_segments = sum(1 for s in segments if s['type'] == 'scan_line')
    transition_segments = sum(1 for s in segments if s['type'] == 'transition')
    
    print(f"Total segments: {total_segments}")
    print(f"Lignes actives: {active_segments} ({active_segments/total_segments*100:.1f}%)")
    print(f"Transitions: {transition_segments} ({transition_segments/total_segments*100:.1f}%)")
    
    # Vérifier l'alternance des directions en mode S
    scan_lines = [s for s in segments if s['type'] == 'scan_line']
    print("\nDirection des lignes de scan (mode S):")
    for i, line in enumerate(scan_lines):
        y_start, y_end = line['start'][1], line['end'][1]
        direction = "→" if y_end > y_start else "←"
        print(f"  Ligne {i}: Y {y_start} {direction} {y_end}")
    
    # Vérifier que les lignes alternent bien
    for i in range(1, len(scan_lines)):
        prev_dir = scan_lines[i-1]['end'][1] - scan_lines[i-1]['start'][1]
        curr_dir = scan_lines[i]['end'][1] - scan_lines[i]['start'][1]
        assert prev_dir * curr_dir < 0, f"Les lignes {i-1} et {i} devraient avoir des directions opposées"
    
    print("✅ Alternance des directions correcte en mode S")


def test_edge_cases():
    """Test des cas limites"""
    print("\n=== Test cas limites ===")
    
    # Scan avec une seule ligne
    print("\n--- Scan avec N=1 ---")
    scan_1 = Scan2DConfigurator(0, 100, 0, 50, 1, mode='E')
    segments_1 = scan_1.get_segmented_trajectory()
    print(f"Segments pour N=1: {len(segments_1)}")
    for seg in segments_1:
        print(f"  {seg['id']}: {seg['type']}")
    assert len([s for s in segments_1 if s['type'] == 'scan_line']) == 1
    
    # Scan avec limites identiques
    print("\n--- Scan avec y_min = y_max ---")
    scan_flat = Scan2DConfigurator(0, 100, 25, 25, 3, mode='E')
    segments_flat = scan_flat.get_segmented_trajectory()
    print(f"Segments pour scan plat: {len(segments_flat)}")
    # Vérifier que toutes les lignes sont horizontales
    for seg in segments_flat:
        if seg['type'] == 'scan_line':
            assert seg['start'][1] == seg['end'][1], "Les lignes devraient être horizontales"
    print("✅ Scan plat géré correctement")


if __name__ == "__main__":
    print("Démarrage des tests du système de segments scan 2D")
    print("="*50)
    
    try:
        test_scan_segments()
        test_segment_identification()
        test_edge_cases()
        
        print("\n" + "="*50)
        print("✅ Tous les tests sont passés avec succès!")
        
    except AssertionError as e:
        print(f"\n❌ Échec du test: {e}")
        raise
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        raise 